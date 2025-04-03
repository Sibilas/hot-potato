import json
import logging
import threading
from proton.handlers import MessagingHandler
from proton.reactor import Container

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class SubscriberHandler(MessagingHandler):
    def __init__(self, amqp_url, enrollment, send_message_callback):
        """
        :param amqp_url: The AMQP URL for the ActiveMQ broker.
        :param enrollment: Dictionary with enrollment details.
                           Expected keys: "id", "queue", "target_url", etc.
        :param send_message_callback: Function that sends an HTTP POST to the enrollment's target URL;
                                      must return an integer HTTP status code.
        """
        super(SubscriberHandler, self).__init__()
        self.amqp_url = amqp_url
        self.enrollment = enrollment
        self.send_message_callback = send_message_callback

    def on_start(self, event):
        logger.info("Subscriber for client '%s': Connecting to AMQP broker at %s", 
                    self.enrollment["id"], self.amqp_url)
        connection = event.container.connect(self.amqp_url)
        logger.info("Subscriber for client '%s': Creating receiver for queue: %s", 
                    self.enrollment["id"], self.enrollment["queue"])
        event.container.create_receiver(connection, self.enrollment["queue"])

    def on_connection_opened(self, event):
        logger.info("Subscriber for client '%s': Connection opened successfully.", 
                    self.enrollment["id"])

    def on_message(self, event):
        message = event.message
        logger.info("Subscriber for client '%s': Received message: %s", 
                    self.enrollment["id"], message.body)
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
                event.delivery.update(event.delivery.ACCEPTED)
                logger.info("Subscriber for client '%s': Message acknowledged (ACK).", 
                            self.enrollment["id"])
            else:
                event.delivery.update(event.delivery.REJECTED)
                logger.info("Subscriber for client '%s': Message rejected (NACK) with status %s", 
                            self.enrollment["id"], status)
        except Exception as e:
            logger.error("Subscriber for client '%s': Error in send_message_callback: %s", 
                         self.enrollment["id"], e)
            event.delivery.update(event.delivery.REJECTED)

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
