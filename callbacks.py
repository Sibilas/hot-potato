import logging
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def send_message_callback(target_url, payload):
    """
    Sends an HTTP POST to the target URL with the provided JSON payload.
    Returns the HTTP status code.
    """
    try:
        response = requests.post(target_url, json=payload, timeout=5)
        logger.info("HTTP POST to %s returned status %s", target_url, response.status_code)
        return response.status_code
    except Exception as e:
        logger.error("HTTP POST to %s failed: %s", target_url, e)
        return 500
