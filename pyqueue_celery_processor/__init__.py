"""
Implementation referred from segment analytics-python
https://github.com/segmentio/analytics-python/tree/master/analytics
"""
import os
from .client import Client

__all__ = ["add_to_queue", "Client"]

default_client = None

"""SETTINGS"""
debug = bool(os.getenv("PYQUEUE_DEBUG", False))
send = bool(os.getenv("PYQUEUE_SEND", True))
max_queue_size = 1_00_000


def add_to_queue(task_func, countdown=0, *args, **kwargs):
    global default_client
    if not default_client:
        default_client = Client(max_queue_size, send, debug)

    default_client.enqueue(task_func, countdown=countdown, args=args, kwargs=kwargs)
