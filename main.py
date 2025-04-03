from dotenv import load_dotenv
load_dotenv(override=True)

import os
import sys
import logging
import subprocess

import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from pydantic import BaseModel
import pyngrok.ngrok as ngrok

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("popdesk")

# --- Environment Variables ---
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 8000))
NGROK_DOMAIN = os.getenv('NGROK_DOMAIN')
NGROK_AUTH_TOKEN = os.getenv('NGROK_AUTH_TOKEN'); assert NGROK_AUTH_TOKEN, "WEBHOOK_PORT must be set in .env file"
WEBHOOK_AUTH_TOKEN = os.getenv('WEBHOOK_AUTH_TOKEN'); assert WEBHOOK_AUTH_TOKEN, "WEBHOOK_AUTH_TOKEN must be set in .env file"

# --- Notification Function ---
def notify_windows(title: str, message: str):
    try:
        title, message = title.replace('"', '`"'), message.replace('"', '`"')
        powershell_command = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);
        $textNodes = $template.GetElementsByTagName("text");
        $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null;
        $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null;
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template);
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("PopDesk");
        $notifier.Show($toast);
        '''
        subprocess.run(["powershell.exe", "-Command", powershell_command], check=True)
        logger.info("Notification sent successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"PowerShell notification failed: {e}")

# --- FastAPI App Setup ---
app = FastAPI(
    title="PopDesk",
    description="A webhook server that triggers desktop notifications",
    version="1.0.0"
)

# --- Pydantic Model ---
class NotificationPayload(BaseModel):
    title: str = "Webhook Notification"
    message: str = "You received a webhook notification!"

# --- Auth Middleware ---
async def verify_auth_header(request: Request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith("Bearer ") or auth_header[7:] != WEBHOOK_AUTH_TOKEN:
        logger.warning(f"Unauthorized: {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

# --- API Routes ---
@app.get("/", status_code=200)
async def health_check():
    return {"status": "healthy", "message": "PopDesk webhook server is running"}

@app.post("/", status_code=200)
async def webhook(payload: NotificationPayload, authorized: bool = Depends(verify_auth_header)):
    notify_windows(title=payload.title, message=payload.message)
    logger.info(f"Notification: '{payload.title}'")
    return {"status": "success"}

# --- Start Server Function ---
def start():
    public_url = "Unavailable"

    # Set up ngrok
    if NGROK_AUTH_TOKEN:
        try:
            ngrok.set_auth_token(NGROK_AUTH_TOKEN)
            logger.info("Ngrok auth token applied.")
        except Exception as e:
            logger.error(f"Ngrok token error: {e}")
    else:
        logger.warning("NGROK_AUTH_TOKEN not set. Using unauthenticated tunnel.")

    try:
        tunnel = ngrok.connect(addr=WEBHOOK_PORT, domain=NGROK_DOMAIN)
        public_url = tunnel.public_url
        logger.info(f"Ngrok tunnel active at {public_url}")
    except Exception as e:
        logger.error(f"Failed to start ngrok tunnel: {e}")
        sys.exit(1)

    # Startup info
    print(f"""\033[92m
PopDesk Webhook Server is RUNNING!
\033[94m
Local URL:  http://localhost:{WEBHOOK_PORT}
Public URL: {public_url}
\033[93m
Send POST requests with:
{{"title": "Your Title", "message": "Your Message"}}
\033[91m
Authorization required: Bearer {WEBHOOK_AUTH_TOKEN}
\033[96m
Test with:
curl -X POST {public_url} \\
    -H "Authorization: Bearer {WEBHOOK_AUTH_TOKEN}" \\
    -H "Content-Type: application/json" \\
    -d '{{"title": "Test", "message": "Hello from curl!"}}'
\033[0m""")

    uvicorn.run(app, host="0.0.0.0", port=WEBHOOK_PORT, log_level="info")

# --- Main Entry Point ---
if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested. Cleaning up...")
        try:
            tunnels = ngrok.get_tunnels()
            for tunnel in tunnels:
                ngrok.disconnect(tunnel.public_url)
            ngrok.kill()
            logger.info("Ngrok tunnels closed cleanly.")
        except Exception as e:
            logger.error(f"Ngrok cleanup error: {e}")
        print("\n\033[92mServer shutdown complete.\033[0m")
        sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error occurred")
        try:
            ngrok.kill()
        except Exception:
            pass
        sys.exit(1)
