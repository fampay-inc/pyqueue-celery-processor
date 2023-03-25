"""
Implementation referred from segment analytics-python
https://github.com/segmentio/analytics-python/tree/master/analytics
"""
import logging
import time
from queue import Empty
from threading import Thread
from pyqueue_celery_processor.metrics import TASKS_PROCESS_SUCCESS, TASKS_PROCESS_FAILED
try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None


class Consumer(Thread):
    """Create a new celery-queue client."""

    log = logging.getLogger("python-celery-queue")

    def __init__(self, queue, debug=False):
        Thread.__init__(self)
        self.daemon = True
        self.running = True
        self.queue = queue
        if debug:
            logging.basicConfig(format="%(threadName)s:%(message)s")
            self.log.setLevel(logging.DEBUG)
            self.log.debug("Python celery queue consumer thread started")

    def run(self):
        self.log.debug("Consumer for celery tasks is running")
        while self.running:
            self.process_queue()
        self.log.debug("Consumer for celery tasks stopped")

    def pause(self):
        # pause polling queue for newer tasks
        self.log.debug("Celery-Queue consumer paused")
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

    def process_task(self, task_item, max_tries=10):
        """Executes a given task item, retries for max_tries times when broker is down
        before dropping a task"""
        task_func = task_item["task_func"]
        countdown = task_item["countdown"]
        args = task_item["args"]
        kwargs = task_item["kwargs"]
        self.log.debug("consuming task: %s | %s | %s", task_func.__name__, args, countdown)
        # retry processing a task for max_tries, else report to sentry
        for retry in range(max_tries):
            try:
                async_result = task_func.apply_async(
                    args=args, kwargs=kwargs, countdown=countdown
                )
                self.log.debug("consumed task: %s | %s | %s | %s", task_func.__name__, args,
                               async_result.id, async_result.status)
                TASKS_PROCESS_SUCCESS.labels(task_name=task_func.__name__).inc()  # pragma: no cover
                return async_result
            except task_func.OperationalError:
                TASKS_PROCESS_FAILED.labels(task_name=task_func.__name__).inc()  # pragma: no cover
                if retry == max_tries - 1:
                    self.log.debug("Task %s dropped, error in broker connection | %s", task_func.__name__, task_item)
                    if sentry_sdk:
                        sentry_sdk.capture_message(
                            "Task dropped, error in broker connection", task_item
                        )
                time.sleep(2)
            except Exception:
                TASKS_PROCESS_FAILED.labels(task_name=task_func.__name__).inc()  # pragma: no cover
                self.log.exception("Error in invoking celery task %s | %s", task_func.__name__, task_item)
                raise ValueError(
                    f"Error in invoking celery task {task_func.__name__}"
                )
