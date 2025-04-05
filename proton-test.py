#!/usr/bin/env python
import sys
import json
import logging
from proton.handlers import MessagingHandler
from proton.reactor import Container

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ProtonTestConsumer")

class ProtonTestConsumer(MessagingHandler):
    def __init__(self, amqp_url, queue):
        # Disable automatic acceptance and settlement to control dispositions manually.
        # super(ProtonTestConsumer, self).__init__(auto_accept=False, auto_settle=False)
        self.amqp_url = amqp_url
        self.queue = queue

    def on_start(self, event):
        logger.debug("on_start: Attempting to connect to %s", self.amqp_url)
        self.conn = event.container.connect(self.amqp_url)
        logger.debug("on_start: Creating receiver for queue: %s", self.queue)
        self.receiver = event.container.create_receiver(self.conn, self.queue)
        # Log receiver properties
        # logger.debug("on_start: Receiver created. auto_accept=%s, auto_settle=%s",
        #              self.receiver.auto_accept, self.receiver.auto_settle)

    def on_connection_opened(self, event):
        logger.debug("on_connection_opened: Connection opened successfully.")

    def on_message(self, event):
        logger.debug("on_message: Received message: %s", event.message.body)
        try:
            payload = event.message.body
            if isinstance(payload, str):
                payload = json.loads(payload)
            logger.debug("on_message: Parsed payload: %s", payload)
        except Exception as e:
            logger.exception("on_message: Exception while parsing message: %s", e)
            payload = event.message.body

        # For testing redelivery, if payload contains "nack": true, we will reject the message.
        if isinstance(payload, dict) and payload.get("nack", False):
            logger.debug("on_message: Rejecting message (calling reject).")
            self.reject(event.delivery)
        else:
            logger.debug("on_message: Accepting message (calling accept).")
            self.accept(event.delivery)

    def on_rejected(self, event):
        logger.debug("on_rejected: Message was rejected by remote peer. Delivery: %s", event.delivery)

    def on_accepted(self, event):
        logger.debug("on_accepted: Message was accepted by remote peer. Delivery: %s", event.delivery)

    def on_settled(self, event):
        logger.debug("on_settled: Message delivery settled. Delivery: %s", event.delivery)

    def on_connection_error(self, event):
        logger.error("on_connection_error: Connection error: %s", getattr(event.connection, "condition", "No condition"))

    def on_transport_error(self, event):
        logger.error("on_transport_error: Transport error: %s", getattr(event.transport, "condition", "No condition"))

    def on_disconnected(self, event):
        logger.debug("on_disconnected: Disconnected from broker.")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python proton-test.py <AMQP_URL> <QUEUE>")
        sys.exit(1)
    amqp_url = sys.argv[1]
    queue = sys.argv[2]

    logger.info("Starting ProtonTestConsumer with AMQP_URL: %s, QUEUE: %s", amqp_url, queue)
    try:
        container = Container(ProtonTestConsumer(amqp_url, queue))
        container.run()
    except KeyboardInterrupt:
        logger.info("Exiting ProtonTestConsumer")
