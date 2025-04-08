import asyncio
import threading
import pytest
from aiohttp import web
import requests

# Import the functions to test from main.py.
from src.main import send_message_callback, start_http_server, start_subscriber_for_enrollment

# A simple fake response class for simulating requests.post.
class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code

# Fake post functions.
def fake_post_success(url, json, timeout):
    return FakeResponse(201)

def fake_post_failure(url, json, timeout):
    raise Exception("Simulated connection error")

def test_send_message_callback_success(monkeypatch):
    # Monkey-patch requests.post to simulate a successful call.
    monkeypatch.setattr(requests, "post", fake_post_success)
    status = send_message_callback("http://dummy-url", {"key": "value"})
    assert status == 201

def test_send_message_callback_failure(monkeypatch):
    # Monkey-patch requests.post to simulate an exception.
    monkeypatch.setattr(requests, "post", fake_post_failure)
    status = send_message_callback("http://dummy-url", {"key": "value"})
    assert status == 500

@pytest.mark.asyncio
async def test_start_http_server(aiohttp_client):
    # Create a dummy app with one endpoint.
    async def hello(request):
        return web.Response(text="Hello, world!")
    app = web.Application()
    app.router.add_get("/hello", hello)

    # Start the server on a test port.
    runner = await start_http_server(app, 8081)
    # Use the aiohttp_client fixture to get a TestClient.
    client = await aiohttp_client(app)
    resp = await client.get("/hello")
    text = await resp.text()
    assert resp.status == 200
    assert text == "Hello, world!"
    await runner.cleanup()

# Global variable to capture subscriber parameters in our dummy run_subscriber.
subscriber_params = None

def dummy_run_subscriber(amqp_url, enrollment, send_message_callback):
    global subscriber_params
    subscriber_params = (amqp_url, enrollment, send_message_callback)

def test_start_subscriber_for_enrollment(monkeypatch):
    # Import main so we can monkey-patch run_subscriber and also override config.
    import src.main as main

    # Create a dummy config object with an AMQP_URL attribute.
    dummy_config = type("DummyConfig", (), {"AMQP_URL": "amqp://dummybroker:5672"})
    main.config = dummy_config

    # Monkey-patch run_subscriber in main with our dummy function.
    monkeypatch.setattr(main, "run_subscriber", dummy_run_subscriber)

    # Create a dummy enrollment.
    enrollment = {
        "id": "test-123",
        "queue": "dummy.queue",
        "target_url": "http://dummy",
        "subscription_args": {}
    }

    # Clear any previous captured parameters.
    global subscriber_params
    subscriber_params = None

    # Call the function under test.
    main.start_subscriber_for_enrollment(enrollment)

    # Verify that our dummy_run_subscriber was called with the expected parameters.
    assert subscriber_params is not None
    amqp_url, enr, callback = subscriber_params
    assert amqp_url == dummy_config.AMQP_URL
    assert enr == enrollment
    # Also verify that the callback passed is the same as main.send_message_callback.
    assert callback == main.send_message_callback
