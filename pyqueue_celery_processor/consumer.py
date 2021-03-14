"""
Implementation referred from segment analytics-python
https://github.com/segmentio/analytics-python/tree/master/analytics
"""
import logging
import time
from queue import Empty
from threading import Thread

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None


class Consumer(Thread):
    """Create a new celery-queue client."""

    log = logging.getLogger("python-celery-queue")

    def __init__(self, queue):
        Thread.__init__(self)
        self.daemon = True
        self.running = True
        self.queue = queue

    def run(self):
        self.log.info("Consumer for celery tasks is running")
        while self.running:
            self.process_queue()
        self.log.info("Consumer for celery tasks stopped")

    def pause(self):
        # pause polling queue for newer tasks
        self.log.info("Celery-Queue consumer paused")
        self.running = False

    def process_queue(self):
        """fetches tasks from queue 1 by 1 and processes them.
        returns when queue is empty"""
        while True:
            try:
                item = self.queue.get(timeout=0.01)
                if item is None:
                    return True
                try:
                    self.process_task(item)
                except ValueError as err:
                    if sentry_sdk:
                        sentry_sdk.capture_message(err.args)
                finally:
                    self.queue.task_done()
            except Empty:
                return
            except Exception as exc:
                if sentry_sdk:
                    sentry_sdk.capture_exception(exc)

    @staticmethod
    def process_task(task_item, max_tries=10):
        """Executes a given task item, retries for max_tries times when broker is down
        before dropping a task"""
        task_func = task_item["task_func"]
        countdown = task_item["countdown"]
        args = task_item["args"]
        kwargs = task_item["kwargs"]
        # retry processing a task for max_tries, else report to sentry
        for retry in range(max_tries):
            try:
                return task_func.apply_async(
                    args=args, kwargs=kwargs, countdown=countdown
                )
            except task_func.OperationalError:
                if retry == max_tries - 1:
                    if sentry_sdk:
                        sentry_sdk.capture_message(
                            "Task dropped, error in broker connection", task_item
                        )
                time.sleep(2)
            except Exception:
                raise ValueError(
                    f"Error in invoking celery task {task_func.__name__}"
                ) from None
