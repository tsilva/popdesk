# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PopDesk is a Python-based webhook server that triggers Windows desktop notifications via HTTP POST requests. It uses FastAPI for the web server and ngrok to expose the local server to the internet.

## Key Architecture

### Single-File Application
The entire application logic is contained in `main.py` with the following key components:

- **FastAPI Application**: Handles HTTP requests with built-in OpenAPI documentation
- **Authorization Middleware**: Bearer token validation via `verify_auth_header()` dependency
- **Notification System**: `notify_windows()` function uses Windows PowerShell to trigger native toast notifications
- **Ngrok Integration**: Automatic tunnel creation on startup to expose the local server publicly

### Request Flow
1. HTTP POST request received at root endpoint `/`
2. Authorization header validated against `WEBHOOK_AUTH_TOKEN`
3. Pydantic model `NotificationPayload` validates JSON payload (title, message)
4. `notify_windows()` triggers PowerShell command to show Windows toast notification
5. Response returned with success status

### Environment Configuration
Required variables in `.env`:
- `WEBHOOK_AUTH_TOKEN`: Bearer token for webhook authentication (required)
- `NGROK_AUTH_TOKEN`: Ngrok authentication token (required)
- `WEBHOOK_PORT`: Server port (default: 8000)
- `NGROK_DOMAIN`: Optional custom ngrok domain

## Common Commands

### Setup
```bash
# Create virtual environment and install dependencies
curl -L https://gist.githubusercontent.com/tsilva/258374c1ba2296d8ba22fffbf640f183/raw/venv-install.sh -o install.sh && chmod +x install.sh && ./install.sh

# Or manually:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run Server
```bash
python main.py
```

The server will:
- Start on configured port (default 8000)
- Establish ngrok tunnel and display public URL
- Print a formatted startup message with test curl command

### Test Notification
```bash
curl -X POST <ngrok-url> \
    -H "Authorization: Bearer <your-token>" \
    -H "Content-Type: application/json" \
    -d '{"title": "Test", "message": "Hello!"}'
```

### Access API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Platform-Specific Constraints

This application is **Windows-only** because:
- The `notify_windows()` function uses PowerShell-specific commands
- It relies on `Windows.UI.Notifications` WinRT APIs
- Desktop notifications are triggered via PowerShell subprocess

## Important Implementation Notes

- The authorization check happens via FastAPI dependency injection in the POST endpoint
- Both GET (health check) and POST (webhook) routes are at the root path `/`
- Ngrok tunnel is automatically cleaned up on KeyboardInterrupt or exceptions
- Quote characters in notification title/message are escaped to prevent PowerShell injection
- The application uses `load_dotenv(override=True)` to ensure `.env` takes precedence

## README Maintenance

README.md must be kept up to date with any significant project changes, including:
- New configuration options or environment variables
- Changes to API endpoints or payload structure
- Platform support modifications
- Setup or usage instructions
