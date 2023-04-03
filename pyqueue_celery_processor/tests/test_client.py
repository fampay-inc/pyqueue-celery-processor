import unittest
from unittest.mock import patch

from pyqueue_celery_processor.client import Client


class TestClient(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_basic_enqueue(self):
        # test enqueuing into the queue
        success, msg = self.client.enqueue(lambda x: x, args=[1])
        self.assertTrue(success)
        self.assertEqual(self.client.queue.qsize(), 1)
        self.assertEqual(msg["args"], [1])
        self.assertEqual(msg["task_func"].__name__, "<lambda>")

    @patch("pyqueue_celery_processor.client.sentry_sdk")
    def test_overflow(self, sentry_mock):
        # keep max_queue_size to one and try to put > 1 items
        client = Client(1)
        client.enqueue(lambda x: x, args=[1])
        success, msg = client.enqueue(lambda x: x, args=[2])
        self.assertFalse(success)
        sentry_mock.capture_message.assert_called_once()

    def test_join(self):
        client = Client(send=False)

        # Test joining the consumer thread when queue is empty
        with patch.object(client.consumer, "join") as mock_consumer_join:
            client.join()
            mock_consumer_join.assert_called_once()

        # Test joining the consumer thread when queue is not empty
        client.queue.put({"task_func": lambda x: x, "args": [1]}, block=False)
        with patch.object(client.consumer, "join") as mock_consumer_join:
            client.join()
            mock_consumer_join.assert_called_once()

    @patch("pyqueue_celery_processor.client.sentry_sdk")
    def test_threshold_exceeded(self, sentry_mock):
        # Test not raising alert when queue size is below threshold
        client = Client(send=True, debug=True, max_queue_size=3)
        client.enqueue(lambda x: x, args=[1])
        sentry_mock.assert_not_called()
