# popdesk

<p align="center">
  <img src="logo.png" alt="PopDesk Logo" width="400"/>
</p>

A simple webhook server that triggers desktop notifications when it receives HTTP requests. This server uses ngrok to expose the webhook endpoint to the internet, making it accessible from anywhere.

## Features

- Receive webhook notifications via HTTP POST requests
- Display desktop notifications with customizable title and message
- Expose the webhook server to the internet using ngrok
- Simple health check endpoint via GET requests
- Secure endpoints with authorization header keys
- FastAPI-powered for better performance and OpenAPI documentation

## Requirements

- Python 3.6+
- Windows operating system (current notification system is Windows-specific)

## Setup

```bash
git clone https://github.com/tsilva/popdesk.git
cd popdesk
chmod +x install.sh
./install.sh
source venv/bin/activate
```

The install script will:
1. Create a virtual environment (or use an existing one)
2. Install dependencies from requirements.txt
3. Create a .env file from .env.example if it doesn't exist

Note: You need to manually activate the virtual environment after the script finishes.

After running the setup script, update your .env file with:
- A secure random string for `WEBHOOK_AUTH_TOKEN` to authenticate webhook requests
- Your ngrok auth token as `NGROK_AUTH_TOKEN` (if you plan to use ngrok)
- Optional: Customize the `PORT` (default: 8000)

### Setting up ngrok (optional)

If you don't already have an ngrok account and authtoken:

1. Sign up at [ngrok.com](https://ngrok.com)
2. Get your authtoken from the ngrok dashboard
3. Add your token to the `.env` file as shown above

## Usage

### Start the server

```bash
python main.py
```

The server will:
1. Start on port 8000 locally (or your configured PORT)
2. Create an ngrok tunnel and display the public URL
3. Run until you press Ctrl+C to exit

### Sending notifications

The server will display a curl command you can use to test the webhook. Generally, you can send a POST request to the ngrok URL:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_webhook_auth_token" \
  -d '{"title": "Test Notification", "message": "Hello from the webhook!"}' \
  <your-ngrok-url>
```

### API Documentation

FastAPI provides automatic API documentation:
- Swagger UI: `http://localhost:{PORT}/docs`
- ReDoc: `http://localhost:{PORT}/redoc`

## Compatibility Note

The current implementation uses Windows-specific notifications via PowerShell. 
Support for other operating systems is planned for future releases.

## How it works

1. The server listens for HTTP POST requests containing JSON payloads
2. The server validates the Authorization header against the configured WEBHOOK_AUTH_TOKEN
3. When a valid request is received, it triggers a Windows desktop notification using PowerShell
4. ngrok creates a secure tunnel to your local server, making it accessible from the internet

## Troubleshooting

- If desktop notifications don't appear, ensure you're using Windows and check your system's notification settings
- If ngrok fails to connect, verify your internet connection and ngrok configuration 
- If you receive 401 Unauthorized errors, check that you're sending the correct authorization header
- For other issues, check the console output for error messages
- If you need API details, check the /docs or /redoc endpoints

## License

[MIT License](LICENSE)
