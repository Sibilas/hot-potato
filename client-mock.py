#!/usr/bin/env python
import asyncio
import logging
from aiohttp import web

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationReceiver")

# Global variable to store the last received message
last_received_message = None

async def receive_message(request):
    global last_received_message
    try:
        data = await request.json()
        logger.info("Received message: %s", data)
        last_received_message = data
        return web.json_response({"status": "received"}, status=200)
    except Exception as e:
        logger.error("Error processing message: %s", e)
        return web.json_response({"error": "Invalid JSON"}, status=400)

async def get_last_message(request):
    if last_received_message is None:
        return web.json_response({"message": "No message received yet."}, status=404)
    return web.json_response({"last_message": last_received_message}, status=200)

def create_app():
    app = web.Application()
    app.add_routes([
        web.post("/receive", receive_message),
        web.get("/last", get_last_message)
    ])
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info("Starting Integration Receiver on port 8089...")
    web.run_app(app, port=8089)
