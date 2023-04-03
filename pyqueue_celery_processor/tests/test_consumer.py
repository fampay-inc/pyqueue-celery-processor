import unittest
import queue

from unittest.mock import Mock, patch

from .tasks import sample_test_task
from pyqueue_celery_processor.consumer import Consumer


class TestConsumer(unittest.TestCase):
    def test_process_queue_empty(self):
        q = queue.Queue()
        consumer = Consumer(q)
        consumer.process_task = Mock()
        consumer.process_queue()
        consumer.process_task.assert_not_called()

    def test_basic_process_task(self):
        q = queue.Queue(0)
        consumer = Consumer(q)
        sample_test_task.apply_async = Mock()
        msg = {
            "task_func": sample_test_task,
            "countdown": 0,
            "args": [1],
            "kwargs": {},
        }
        consumer.process_task(msg)
        sample_test_task.apply_async.assert_called_once()

    def test_process_task_successful(self):
        task = {
            "task_func": Mock(),
            "countdown": 0,
            "args": [],
            "kwargs": {}
        }
        q = queue.Queue()
        q.put(task)
        consumer = Consumer(q)
        consumer.process_task = Mock()
        consumer.process_queue()
        consumer.process_task.assert_called_once_with(task)

    def test_process_task_exception(self):
        q = queue.Queue(0)
        consumer = Consumer(q)
        sample_test_task.apply_async = Mock(side_effect=Exception)
        msg = {
            "task_func": sample_test_task,
            "countdown": 0,
            "args": [1],
            "kwargs": {},
        }
        self.assertRaises(ValueError, consumer.process_task, msg)

    @patch("pyqueue_celery_processor.consumer.sentry_sdk")
    def test_sentry_invoked(self, sentry_mock):
        q = queue.Queue(1)
        consumer = Consumer(q)
        sample_test_task.apply_async = Mock(side_effect=Exception)
        msg = {
            "task_func": sample_test_task,
            "countdown": 0,
            "args": [1],
            "kwargs": {},
        }
        q.put(msg)
        consumer.process_queue()
        sentry_mock.capture_message.assert_called_once_with(
            ("Error in invoking celery task sample_test_task",)
        )

    @patch("pyqueue_celery_processor.consumer.sentry_sdk")
    def test_connection_retries(self, sentry_mock):
        q = queue.Queue(1)
        consumer = Consumer(q)
        sample_test_task.apply_async = Mock(
            side_effect=sample_test_task.OperationalError
        )
        msg = {
            "task_func": sample_test_task,
            "countdown": 0,
            "args": [1],
            "kwargs": {},
        }
        q.put(msg)
        consumer.process_task(msg, 1)
        sentry_mock.capture_message.assert_called_once_with(
            "Task dropped, error in broker connection", msg
        )
