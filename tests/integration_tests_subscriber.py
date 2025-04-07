import json
import threading
import time
import logging
import pytest

from proton import Message
from proton.reactor import Container
from proton.handlers import MessagingHandler
from src.consumerMQ.subscriber import run_subscriber

# Configure logging for integration tests.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("integration_tests")

# Global list to record messages received via the HTTP callback.
received_messages = []

# Integration HTTP callback that simulates a successful HTTP POST.
def integration_send_message(url, payload):
    logger.info("integration_send_message called with url: %s, payload: %s", url, payload)
    received_messages.append(payload)
    return 200

# Enrollment information used by the subscriber.
enrollment = {
    "target_url": "http://example.com/integration",  # Dummy URL for integration test.
    "queue": "test.integration.queue",
    "subscription_args": {}
}

# Local ActiveMQ broker URL.
broker_url = "amqp://192.168.15.22:5672"

# A simple MessagingHandler to send a test message.
class SenderHandler(MessagingHandler):
    def __init__(self, broker_url, queue, message_body):
        super(SenderHandler, self).__init__()
        self.broker_url = broker_url
        self.queue = queue
        self.message_body = message_body

    def on_start(self, event):
        conn = event.container.connect(self.broker_url)
        sender = event.container.create_sender(conn, self.queue)
        msg = Message(body=self.message_body)
        sender.send(msg)
        logger.info("Sent test message: %s", self.message_body)
        event.container.stop()

# Fixture to start the subscriber in a daemon thread.
@pytest.fixture(scope="module")
def subscriber_thread():
    thread = threading.Thread(
        target=run_subscriber,
        args=(broker_url, enrollment, integration_send_message),
        daemon=True
    )
    thread.start()
    # Allow time for the subscriber to connect.
    time.sleep(3)
    yield
    # (The daemon thread will exit when the main test process exits.)

def test_integration_subscriber(subscriber_thread):
    global received_messages
    received_messages.clear()

    # Prepare a test payload.
    test_payload = {"integration": "test", "value": 123}
    message_body = json.dumps(test_payload)

    # Use a Proton sender to send a test message to the enrollment queue.
    sender_handler = SenderHandler(broker_url, enrollment["queue"], message_body)
    Container(sender_handler).run()

    # Wait up to 10 seconds for the subscriber to process the message.
    timeout = 10
    start_time = time.time()
    while time.time() - start_time < timeout:
        if received_messages:
            break
        time.sleep(1)

    assert received_messages, "No messages received by the subscriber integration callback."
    assert test_payload == received_messages[0], "Received message payload does not match expected."

if __name__ == '__main__':
    import sys
    sys.exit(pytest.main([__file__]))
