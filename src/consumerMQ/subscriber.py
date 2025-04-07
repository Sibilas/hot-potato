import json
import logging
import threading
from proton.handlers import MessagingHandler, TransactionHandler
from proton.reactor import Container
from proton import Disposition, Receiver

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class SubscriberHandler(MessagingHandler, TransactionHandler):
    def __init__(self, amqp_url, enrollment, send_message_callback):
        """
        :param amqp_url: The AMQP URL for the ActiveMQ broker.
        :param enrollment: Dictionary with enrollment details.
                           Expected keys: "id", "queue", "target_url", etc.
        :param send_message_callback: Function that sends an HTTP POST to the enrollment's target URL;
                                      must return an integer HTTP status code.
        """
        # Disable auto_accept and auto_settle so that we control the message disposition explicitly.
        super(SubscriberHandler, self).__init__(auto_accept=False, auto_settle=False)
        self.amqp_url = amqp_url
        self.enrollment = enrollment
        self.send_message_callback = send_message_callback

    def on_start(self, event):
        logger.info("Subscriber for client '%s': Connecting to AMQP broker at %s", 
                    self.enrollment["id"], self.amqp_url)
        connection = event.container.connect(self.amqp_url)
        logger.info("Subscriber for client '%s': Creating receiver for queue: %s", 
                    self.enrollment["id"], self.enrollment["queue"])
        # Create receiver normally; auto_settle is disabled by our constructor.
        event.container.create_receiver(connection, self.enrollment["queue"])

    def on_connection_opened(self, event):
        logger.info("Subscriber for client '%s': Connection opened successfully.", 
                    self.enrollment["id"])
    def on_rejected(self, event):
        logger.debug("on_rejected: Message was rejected by remote peer. Delivery: %s", event.delivery)

    def on_accepted(self, event):
        logger.debug("on_accepted: Message was accepted by remote peer. Delivery: %s", event.delivery)
    
    def on_released(self, event):
        logger.debug("on_released: Message was RELEASED by remote peer. Delivery: %s", event)

    def on_settled(self, event):
        logger.debug("on_settled: Message delivery settled. Delivery: %s", event.delivery)

    def on_message(self, event):
        message = event.message
        logger.info("Subscriber for client '%s': Received message: %s", 
                    self.enrollment["id"], message.body)
        print(f"EVENT: {event}")
        try:
            payload = message.body
            if isinstance(payload, str):
                payload = json.loads(payload)
        except Exception as e:
            logger.error("Subscriber for client '%s': Failed to parse message: %s", 
                         self.enrollment["id"], e)
            payload = message.body

        try:
            status = self.send_message_callback(self.enrollment["target_url"], payload)
            if 200 <= status < 300:
                # Explicitly accept the message
                self.accept(event.delivery)
                logger.info("Subscriber for client '%s': Message accepted (ACK).", 
                            self.enrollment["id"])
            else:
                # Explicitly reject the message
                local_state = event.delivery.local
                local_state.failed = True
                local_state.undeliverable = False
                event.delivery.update(local_state.type)
                self.settle(event.delivery, event.delivery.MODIFIED)
                logger.info("Subscriber for client '%s': Message.RELEASED (NACK) with status %s", 
                            self.enrollment["id"], status)
        except Exception as e:
            logger.error("Subscriber for client '%s': Error in send_message_callback: %s", 
                         self.enrollment["id"], e)
            # Explicitly reject the message
            local_state = event.delivery.local
            local_state.failed = True
            local_state.undeliverable = False
            event.delivery.update(local_state.type)
            self.settle(event.delivery, event.delivery.MODIFIED)

class SubscriberRunner:
    """
    Wraps a subscriber in its own thread to provide an independent AMQP connection per enrollment.
    """
    def __init__(self, amqp_url, enrollment, send_message_callback):
        self.amqp_url = amqp_url
        self.enrollment = enrollment
        self.send_message_callback = send_message_callback
        self.container = None
        self.thread = None

    def start(self):
        def run_container():
            handler = SubscriberHandler(self.amqp_url, self.enrollment, self.send_message_callback)
            self.container = Container(handler)
            try:
                self.container.run()
            except Exception as e:
                logger.error("Subscriber for client '%s' terminated with error: %s", 
                             self.enrollment["id"], e)
        self.thread = threading.Thread(target=run_container, daemon=True)
        self.thread.start()

    def stop(self):
        if self.container:
            try:
                self.container.stop()
                logger.info("Subscriber for client '%s': Stopped.", self.enrollment["id"])
            except Exception as e:
                logger.error("Error stopping subscriber for client '%s': %s", 
                             self.enrollment["id"], e)
        else:
            logger.warning("No active container to stop for client '%s'.", self.enrollment["id"])

def run_subscriber(amqp_url, enrollment, send_message_callback):
    """
    Convenience function that creates and starts a SubscriberRunner.
    Returns the runner instance so it can be stopped later.
    """
    runner = SubscriberRunner(amqp_url, enrollment, send_message_callback)
    runner.start()
    return runner
