<div align="center">
  <img src="logo.png" alt="popdesk" width="200"/>

  # popdesk

  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
  [![Python 3.6+](https://img.shields.io/badge/Python-3.6+-3776AB.svg)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-009688.svg)](https://fastapi.tiangolo.com/)

  **🔔 Trigger Windows desktop notifications from anywhere via webhooks 🌐**

  [API Docs](#-api-documentation) · [Setup](#-setup) · [Usage](#-usage)
</div>

---

## Overview

PopDesk is a lightweight webhook server that displays Windows toast notifications when it receives HTTP requests. It uses ngrok to expose your local server to the internet, letting you trigger notifications from CI/CD pipelines, monitoring systems, or any service that can send HTTP requests.

## Features

- **Remote notifications** — Trigger Windows desktop alerts from anywhere via HTTP POST
- **Public URL via ngrok** — Automatic tunnel creation exposes your webhook to the internet
- **Bearer token auth** — Secure your endpoint with simple token-based authentication
- **FastAPI-powered** — Built-in OpenAPI docs, request validation, and async support
- **Health checks** — GET endpoint for monitoring server status

## Quick Start

```bash
# Clone and install
git clone https://github.com/tsilva/popdesk.git
cd popdesk
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your tokens

# Run
python main.py
```

## Setup

### Requirements

- Python 3.6+
- Windows OS (uses native Windows toast notifications)
- [ngrok account](https://ngrok.com) (free tier works)

### Environment Variables

Create a `.env` file with the following:

| Variable | Required | Description |
|----------|----------|-------------|
| `WEBHOOK_AUTH_TOKEN` | Yes | Bearer token for webhook authentication |
| `NGROK_AUTH_TOKEN` | Yes | Your ngrok authentication token |
| `WEBHOOK_PORT` | No | Server port (default: `8000`) |
| `NGROK_DOMAIN` | No | Custom ngrok domain (if you have one) |

### Installation Options

**Option 1: Manual setup**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Option 2: Using install script**
```bash
curl -L https://gist.githubusercontent.com/tsilva/258374c1ba2296d8ba22fffbf640f183/raw/venv-install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

## Usage

### Start the Server

```bash
python main.py
```

The server will:
- Start on the configured port (default 8000)
- Establish an ngrok tunnel and display the public URL
- Print a test curl command with your auth token

### Send a Notification

```bash
curl -X POST <your-ngrok-url> \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello!", "message": "This is a test notification"}'
```

### API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | No | Health check endpoint |
| `POST` | `/` | Yes | Trigger a notification |

### Request Payload

```json
{
  "title": "Notification Title",
  "message": "Notification message body"
}
```

Both fields have defaults, so an empty `{}` payload will still trigger a notification.

## API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No notification appears | Ensure you're running on Windows and check notification settings |
| 401 Unauthorized | Verify your `Authorization: Bearer <token>` header matches `.env` |
| ngrok tunnel fails | Check your internet connection and `NGROK_AUTH_TOKEN` |
| Port already in use | Change `WEBHOOK_PORT` in `.env` or stop the conflicting process |

## License

[MIT](LICENSE)
