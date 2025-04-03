import asyncio
import logging
import threading
import requests
from aiohttp import web

from config import load_config
from enroll import create_app
from subscriptions import start_subscriber_for_enrollment  # New module for subscriber management
from database import db_manager
from callbacks import send_message_callback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_http_server(app, port):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=port)
    await site.start()
    logger.info("HTTP server started on port %s", port)
    return runner

if __name__ == '__main__':
    config = load_config()
    logger.info("Loaded configuration: %s", config)

    app = create_app()
    loop = asyncio.get_event_loop()
    runner = loop.run_until_complete(start_http_server(app, config.HTTP_PORT))

    # Start subscribers for existing enrollments.
    enrollments = db_manager.query("SELECT * FROM enrollments")
    for row in enrollments:
        enrollment = dict(row)
        start_subscriber_for_enrollment(config.AMQP_URL, enrollment, send_message_callback)

    try:
        logger.info("hot-potato service running. Press Ctrl+C to exit.")
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down hot-potato service.")
    finally:
        loop.run_until_complete(runner.cleanup())
        db_manager.backup_to_disk()
        db_manager.close()
