"""
Implementation referred from segment analytics-python
https://github.com/segmentio/analytics-python/tree/master/analytics
"""
from .client import Client

default_client = None

"""SETTINGS"""
send = True
max_queue_size = 1_00_000
__all__ = ["add_to_queue"]


def add_to_queue(task_func, countdown=0, *args, **kwargs):
    global default_client
    if not default_client:
        default_client = Client(max_queue_size, send)

    default_client.enqueue(task_func, countdown=countdown, args=args, kwargs=kwargs)
