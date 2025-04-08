import json
import uuid
import logging
from aiohttp import web
from src.database.database import db_manager
from src.consumerMQ.subscriptions import start_subscriber_for_enrollment
from src.callbacks import send_message_callback

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def handle_enroll(request):
    """
    POST /enroll endpoint.
    Expected JSON payload:
      {
        "queue": "chat.test",
        "target_url": "http://client-service/receive",
        "subscription_args": { ... }
      }
    """
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON payload"}, status=400)

    for field in ["queue", "target_url"]:
        if field not in data:
            return web.json_response({"error": f"Missing required field: {field}"}, status=400)

    enrollment_id = str(uuid.uuid4())
    queue = data["queue"]
    target_url = data["target_url"]
    subscription_args = json.dumps(data.get("subscription_args", {}))

    try:
        db_manager.execute(
            "INSERT OR REPLACE INTO enrollments (id, queue, target_url, subscription_args) VALUES (?, ?, ?, ?)",
            (enrollment_id, queue, target_url, subscription_args)
        )
    except Exception as e:
        logger.error("Error inserting enrollment: %s", e)
        return web.json_response({"error": "Database insertion failed"}, status=500)

    enrollment = {
        "id": enrollment_id,
        "queue": queue,
        "target_url": target_url,
        "subscription_args": json.loads(subscription_args)
    }
    logger.info("Enrollment created: %s", enrollment_id)
    
    # Start a new subscriber for this enrollment.
    from src.config import load_config
    config = load_config()
    start_subscriber_for_enrollment(config.AMQP_URL, enrollment, send_message_callback)

    return web.json_response(enrollment, status=201)

async def handle_delete_enrollment(request):
    """
    DELETE /enroll/{id} endpoint.
    """
    enrollment_id = request.match_info.get("id")
    try:
        db_manager.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))
    except Exception as e:
        logger.error("Error deleting enrollment: %s", e)
        return web.json_response({"error": "Failed to delete enrollment"}, status=500)

    logger.info("Enrollment deleted: %s", enrollment_id)
    from src.consumerMQ.subscriptions import stop_subscriber_for_enrollment
    stop_subscriber_for_enrollment(enrollment_id)
    return web.json_response({"message": f"Enrollment {enrollment_id} deleted"}, status=200)

async def handle_list_enrollments(request):
    try:
        rows = db_manager.query("SELECT * FROM enrollments")
        enrollments = [dict(row) for row in rows]
        # Convert subscription_args from JSON string back to dict.
        for enrollment in enrollments:
            try:
                enrollment["subscription_args"] = json.loads(enrollment["subscription_args"]) if enrollment["subscription_args"] else {}
            except Exception:
                enrollment["subscription_args"] = {}
        return web.json_response(enrollments)
    except Exception as e:
        logger.error("Error fetching enrollments: %s", e)
        return web.json_response({"error": "Failed to fetch enrollments"}, status=500)

def create_app():
    app = web.Application()
    app.add_routes([
        web.post("/enroll", handle_enroll),
        web.get("/enrollments", handle_list_enrollments),
        web.delete("/enroll/{id}", handle_delete_enrollment)
    ])
    return app
