"""
Implementation referred from segment analytics-python
https://github.com/segmentio/analytics-python/tree/master/analytics
"""
import atexit
import logging
import queue

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None
from .consumer import Consumer
from .metrics import (
    CONSUMER_STOPPED_GRACEFULLY,
    TASKS_ENQUEUE_TOTAL,
    TASKS_ENQUEUE_FAILED_TOTAL,
)


LOGGER = logging.getLogger("python-celery-queue")


class Client(object):
    """Create a new celery-queue client."""

    threshold_size = 10_000

    def __init__(self, max_queue_size=1_00_000, send=True, debug=False):
        self.queue = queue.Queue(max_queue_size)
        self.send = send
        self.threshold_exceeded = False
        LOGGER.info("Python celery queue initialised")
        # Pauses polling the queue and processes left tasks
        if send:
            atexit.register(self.join)

        self.consumer = Consumer(self.queue, debug)
        if send:
            self.consumer.start()

    def enqueue(self, task_func, countdown=0, args=None, kwargs=None):
        """Publishes the task into the queue.
        Drops the task if queue size reaches max limit"""
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        LOGGER.info("enqueued task: %s | %s", task_func.__name__, args)
        msg = {
            "task_func": task_func,
            "countdown": countdown,
            "args": args,
            "kwargs": kwargs,
        }
        if not self.send:
            return True, msg

        # Raise alert everytime queue size exceeds the threshold size
        size = self.queue.qsize()
        if size > self.threshold_size and not self.threshold_exceeded:
            self.threshold_exceeded = True
            LOGGER.info("Celery task %s queue size exceeded threshold. Size: %s | %s", task_func.__name__, size, args)
            if sentry_sdk:
                sentry_sdk.capture_message(
                    f"Celery task queue size exceeded threshold. Size:{size}"
                )
        if size <= self.threshold_size:
            self.threshold_exceeded = False
        # add to queue
        try:
            self.queue.put(msg, block=False)
            TASKS_ENQUEUE_TOTAL.labels(task_name=task_func.__name__).inc()  # pragma: no cover
            return True, msg
        except queue.Full:
            LOGGER.info("Task %s dropped, internal queue max limit reached | %s", task_func.__name__, args)
            if sentry_sdk:
                sentry_sdk.capture_message(
                    "Task dropped, internal queue max limit reached", msg
                )
            TASKS_ENQUEUE_FAILED_TOTAL.labels(task_name=task_func.__name__).inc()  # pragma: no cover
            return False, msg

    def join(self):
        """Exits the consumer thread once queue is empty.
        Blocks main thread until secondary thread completes
        """
        LOGGER.info("Exiting python celery queue")
        self.consumer.pause()
        try:
            self.consumer.join()
            CONSUMER_STOPPED_GRACEFULLY.inc()  # pragma: no cover
            LOGGER.info("Consumer stopped gracefully")
        except RuntimeError:
            LOGGER.info("consumer thread not running")
        except Exception as e:
            LOGGER.info("Unexpected exception occured while trying to stop consumer gracefully. Exception: %s", str(e))
