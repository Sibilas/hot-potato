import logging
from subscriber import SubscriberRunner

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global registry for active subscriber runners.
active_subscribers = {}

def start_subscriber_for_enrollment(amqp_url, enrollment, send_message_callback):
    """
    Starts a new SubscriberRunner for the given enrollment.
    Returns the runner instance.
    """
    runner = SubscriberRunner(amqp_url, enrollment, send_message_callback)
    runner.start()
    active_subscribers[enrollment["id"]] = runner
    logger.info("Started subscriber for enrollment: %s", enrollment["id"])
    return runner

def stop_subscriber_for_enrollment(enrollment_id):
    """
    Stops the subscriber runner associated with the given enrollment ID and removes it from the registry.
    """
    runner = active_subscribers.pop(enrollment_id, None)
    if runner:
        runner.stop()
        logger.info("Stopped subscriber for enrollment: %s", enrollment_id)
    else:
        logger.warning("No active subscriber found for enrollment: %s", enrollment_id)
