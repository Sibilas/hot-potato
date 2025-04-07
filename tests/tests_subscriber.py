import json
import pytest
from src.consumerMQ.subscriber import SubscriberHandler

sibimq_url = "amqp://192.168.15.22:5672"
# Dummy classes to simulate Proton event, message, and delivery objects.
class DummyDelivery:
    # Mimic the delivery constants as attributes.
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    RELEASED = "RELEASED"
    
    def __init__(self):
        self.status = None

    def update(self, status):
        self.status = status

class DummyMessage:
    def __init__(self, body):
        self.body = body

class DummyEvent:
    def __init__(self, message, delivery):
        self.message = message
        self.delivery = delivery
        # In Proton, the delivery object normally has the constants. We simulate that here:
        self.delivery.ACCEPTED = DummyDelivery.ACCEPTED
        self.delivery.REJECTED = DummyDelivery.REJECTED
        self.delivery.RELEASED = DummyDelivery.RELEASED

# Fake HTTP callback that simulates a successful (200) response.
def fake_send_message_success(url, payload):
    return 200

# Fake HTTP callback that simulates a failure (e.g., 500).
def fake_send_message_failure(url, payload):
    return 500

def test_on_message_success():
    enrollment = {"target_url": "http://example.com/api", "queue": "chat.test"}
    handler = SubscriberHandler(sibimq_url, enrollment, fake_send_message_success)
    message_body = json.dumps({"key": "value"})
    message = DummyMessage(message_body)
    delivery = DummyDelivery()
    event = DummyEvent(message, delivery)
    handler.on_message(event)
    assert delivery.status == DummyDelivery.ACCEPTED

def test_on_message_failure():
    enrollment = {"target_url": "http://example.com/api", "queue": "chat.test"}
    handler = SubscriberHandler(sibimq_url, enrollment, fake_send_message_failure)
    message_body = json.dumps({"key": "value"})
    message = DummyMessage(message_body)
    delivery = DummyDelivery()
    event = DummyEvent(message, delivery)
    handler.on_message(event)
    assert delivery.status == DummyDelivery.REJECTED

def test_on_message_invalid_json():
    # Even if JSON parsing fails, the callback is still invoked.
    enrollment = {"target_url": "http://example.com/api", "queue": "chat.test"}
    handler = SubscriberHandler(sibimq_url, enrollment, fake_send_message_success)
    # Provide an invalid JSON string.
    message_body = "not a valid json"
    message = DummyMessage(message_body)
    delivery = DummyDelivery()
    event = DummyEvent(message, delivery)
    handler.on_message(event)
    # With fake_send_message_success, a 200 is returned even with invalid JSON.
    assert delivery.status == DummyDelivery.ACCEPTED

if __name__ == '__main__':
    import sys
    sys.exit(pytest.main([__file__]))
