import logging
from proton.handlers import MessagingHandler
from proton.reactor import Container

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ActiveMQConnector")

class ActiveMQConnector(MessagingHandler):
    def __init__(self, amqp_url):
        super(ActiveMQConnector, self).__init__()
        self.amqp_url = amqp_url

    def on_start(self, event):
        logger.info("Attempting to connect to %s", self.amqp_url)
        event.container.connect(self.amqp_url)

    def on_connection_opened(self, event):
        logger.info("Connection opened successfully to %s", self.amqp_url)

    def on_transport_error(self, event):
        condition = getattr(event.transport, 'condition', None)
        logger.error("Transport error: %s", condition)

    def on_connection_error(self, event):
        condition = getattr(event.connection, 'condition', None)
        logger.error("Connection error: %s", condition)

if __name__ == '__main__':
    # Append an idleTimeout parameter to help maintain the connection.
    broker_url = "amqp://192.168.15.22:5672?amqp.idleTimeout=60000"
    connector = ActiveMQConnector(broker_url)
    Container(connector).run()
