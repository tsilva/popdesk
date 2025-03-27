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

## Requirements

- Python 3.6+
- Dependencies listed in `requirements.txt`

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/tsilva/popdesk.git
cd popdesk
```

### 2. Create a virtual environment using venv

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

### 3. Install dependencies with uv

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver. To install it:

```bash
pip install uv
```

Then install the project dependencies:

```bash
uv pip install -r requirements.txt
```

Alternatively, you can use pip directly:

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root with the following content:

```
AUTH_KEY=your_secret_key_here
NGROK_AUTH_TOKEN=your_ngrok_auth_token
```

Replace `your_secret_key_here` with a secure random string to authenticate webhook requests.
Replace `your_ngrok_auth_token` with your ngrok auth token if you plan to use ngrok.

### 5. Setting up ngrok (optional)

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
1. Start on port 8000 locally
2. Create an ngrok tunnel and display the public URL
3. Run until you press Enter to exit

### Sending notifications

Send a POST request to the ngrok URL displayed in the console:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_secret_key_here" \
  -d '{"title": "Test Notification", "message": "Hello from the webhook!"}' \
  <your-ngrok-url>
```

## How it works

1. The server listens for HTTP POST requests containing JSON payloads
2. The server validates the Authorization header against the configured AUTH_KEY
3. When a valid request is received, it triggers a desktop notification using the plyer library
4. ngrok creates a secure tunnel to your local server, making it accessible from the internet

## Troubleshooting

- If desktop notifications don't appear, check your system's notification settings
- If ngrok fails to connect, verify your internet connection and ngrok configuration 
- If you receive 401 Unauthorized errors, check that you're sending the correct authorization header
- For other issues, check the console output for error messages

## License

[MIT License](LICENSE)
