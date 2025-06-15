# 🥔 Hot-Potato (test github)

**Hot-Potato** is a lightweight and resilient message dispatching service that listens to an AMQP 1.0 message broker (like ActiveMQ Artemis), receives messages from queues (addresses), and **forwards** them to HTTP services (clients) based on dynamic runtime enrollment.

If a message can't be delivered to a client (e.g., service down), the message is **NACKed** and **retried** by the broker, eventually being sent to the **DLQ (Dead Letter Queue)** when the max delivery attempts are exceeded.

---

## 🌐 Concept

- A **client** enrolls itself to receive messages from a specific **queue/address** on the broker.
- Hot-Potato keeps an **in-memory database** of enrollments and syncs with **disk (SQLite)** to persist state.
- Each client has its **own independent AMQP receiver and thread**, ensuring isolation and resilience.
- Messages are **acknowledged (ACK)** only when successfully posted to the client.
- On failure (non-2xx response), the message is **NACKed (released with delivery=True)**, letting the broker retry or send to DLQ.

---

## 📁 File Structure

```bash
hot-potato/
├── main.py                   # Application entrypoint: loads config, starts HTTP server and subscribers
├── enroll.py                 # Aiohttp server: exposes HTTP API to enroll, list, delete clients
├── subscriber.py             # AMQP subscriber logic using Qpid Proton
├── callbacks.py              # Helper for sending messages to clients over HTTP
├── subscriptions.py          # Manages active subscribers (start/stop logic)
├── database/                 # In-memory + disk SQLite management
├── config.py                 # Loads environment variables and config
├── utils.py                  # JSON validation, logging config
├── test_service.py           # Dummy HTTP server used for integration testing (port 8089)
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker container setup (optional)
└── README.md                 # You're here 😄

🚀 How to Run (Local)
1. Clone the Repository
git clone https://github.com/your-org/hot-potato.git
cd hot-potato

2. Create and Activate Virtual Environment
python3 -m venv venv
source venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt

4. Start ActiveMQ Artemis
Make sure you have a broker running on:
amqp://admin:admin@localhost:5672

5. Run Hot-Potato
python main.py

6. (Optional) Run Integration Test Server
python test_service.py
This runs a dummy HTTP server on port 8089 that simulates a client receiving messages.

🧪 Example API Usage
✅ Enroll a client:
POST http://localhost:8080/enroll
Content-Type: application/json

{
  "queue": "chat",
  "target_url": "http://localhost:8089/receive",
  "subscription_args": {
    "durable": true
  }
}

📜 List all enrollments:
GET http://localhost:8080/enrollments

❌ Delete an enrollment:
DELETE http://localhost:8080/enroll/{id}

⚙️ Configuration (Environment Variables)
Variable	Default	Description
AMQP_URL	amqp://localhost:5672	AMQP 1.0 broker connection URL
HTTP_PORT	8080	Port to expose the HTTP API
SQLITE_BACKUP_PATH	hotpotato.sqlite	Path to persist enrollment data
LOG_LEVEL	INFO	Log level (DEBUG, INFO, etc.)
Set these manually or via a .env file.

🔍 Features
✅ Isolated connections per client (no interference)

✅ Dynamic client registration via REST API

✅ Persisted enrollments (disk+RAM sync)

✅ Ack/Nack with retry logic and DLQ fallback

✅ Integration-ready with custom HTTP services

✅ Clean logs and modular design

🔧 Roadmap Ideas
 GUI dashboard to visualize clients and queue activity

 Health check endpoints (/health)

 Rate limiting / retry backoff strategies

 Stats endpoint (delivered, retries, failed)

 Optional headers and auth for client POSTs

🤝 Contributions
Found a bug? Got a feature idea? Open an issue or send a pull request!

