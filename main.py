import os
import sys
import uvicorn
import subprocess
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException, status
from pydantic import BaseModel
import pyngrok.ngrok as ngrok
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Notification via PowerShell ---
def notify_windows(title: str, message: str):
    try:
        # Escape quotes
        safe_title = title.replace('"', '`"')
        safe_message = message.replace('"', '`"')
        powershell_command = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);
        $textNodes = $template.GetElementsByTagName("text");
        $textNodes.Item(0).AppendChild($template.CreateTextNode("{safe_title}")) > $null;
        $textNodes.Item(1).AppendChild($template.CreateTextNode("{safe_message}")) > $null;
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template);
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("PopDesk");
        $notifier.Show($toast);
        '''
        subprocess.run(["powershell.exe", "-Command", powershell_command], check=True)
        logger.info("Notification sent to Windows via PowerShell.")
    except subprocess.CalledProcessError as e:
        logger.error(f"PowerShell notification failed: {e}")

# --- Validate environment variables ---
def validate_env_vars():
    placeholder_values = {
        'NGROK_AUTH_TOKEN': ['your-ngrok-auth-token'],
        'WEBHOOK_AUTH_TOKEN': ['your-webhook-auth-token']
    }

    errors = []

    for var, placeholders in placeholder_values.items():
        value = os.getenv(var)
        if not value:
            errors.append(f"Environment variable {var} is not set.")
        elif value.lower() in [p.lower() for p in placeholders]:
            errors.append(f"Environment variable {var} still contains a placeholder value '{value}'. Please update it with your actual credentials.")

    port_str = os.getenv('PORT', '8000')
    if not port_str.isdigit():
         errors.append(f"Environment variable PORT ('{port_str}') is not a valid integer.")
    elif not (1 <= int(port_str) <= 65535):
         errors.append(f"Environment variable PORT ('{port_str}') is not within the valid range (1-65535).")

    if errors:
        print("\033[91m" + "Error: Environment configuration not complete!" + "\033[0m")
        for error in errors:
            print("\033[93m" + f" - {error}" + "\033[0m")
        print("\033[93m" + "Please update your .env file with your actual values before running the application." + "\033[0m")
        print("\033[93m" + "If you haven't created a .env file yet, run the install script or copy .env.example to .env first." + "\033[0m")
        sys.exit(1)

validate_env_vars()

# --- Models ---
class NotificationPayload(BaseModel):
    title: Optional[str] = "Webhook Notification"
    message: Optional[str] = "You received a webhook notification!"

# --- FastAPI app ---
app = FastAPI(
    title="PopDesk",
    description="A webhook server that triggers desktop notifications",
    version="1.0.0"
)

# --- Environment ---
PORT = int(os.getenv('PORT', 8000))
NGROK_AUTH_TOKEN = os.getenv('NGROK_AUTH_TOKEN')
WEBHOOK_AUTH_TOKEN = os.getenv('WEBHOOK_AUTH_TOKEN')

# --- Set up ngrok ---
if NGROK_AUTH_TOKEN:
    try:
        ngrok.set_auth_token(NGROK_AUTH_TOKEN)
        logger.info("Ngrok auth token set.")
    except Exception as e:
        logger.error(f"Failed to set ngrok auth token: {e}")
else:
    logger.warning("NGROK_AUTH_TOKEN is not set. Ngrok connection might be limited or fail.")

# --- Auth Dependency ---
async def verify_auth_header(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer ') or auth_header.split(' ')[1] != WEBHOOK_AUTH_TOKEN:
        logger.warning(f"Unauthorized access attempt from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

# --- Routes ---
@app.get("/", status_code=200)
async def health_check():
    return {"status": "healthy", "message": "PopDesk webhook server is running"}

@app.post("/", status_code=200)
async def webhook(payload: NotificationPayload, authorized: bool = Depends(verify_auth_header)):
    if not authorized:
        return

    try:
        notify_windows(
            title=payload.title or "Webhook Notification",
            message=payload.message or "You received a webhook notification!"
        )

        logger.info(f"Notification displayed: Title='{payload.title}'")
        return {"status": "success", "message": "Notification sent"}

    except Exception as e:
        logger.error(f"Error processing or displaying notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error processing notification: {str(e)}")

# --- Start Server ---
def start():
    public_url = None
    try:
        logger.info(f"Attempting to establish ngrok tunnel on port {PORT}...")
        http_tunnel = ngrok.connect(PORT)
        public_url = http_tunnel.public_url
        logger.info(f"Ngrok tunnel established successfully at: {public_url}")
    except Exception as e:
        logger.error(f"FATAL: Failed to establish ngrok tunnel: {e}")
        print("\033[91mError: Could not start ngrok tunnel.\033[0m")
        print("\033[93m  Reason:", e, "\033[0m")
        sys.exit(1)

    logger.info(f"Starting PopDesk webhook server on http://0.0.0.0:{PORT}")
    print("\033[92m\nPopDesk Webhook Server is RUNNING!\033[0m")
    print(f"\033[94mLocal URL:  http://localhost:{PORT}\033[0m")
    print(f"\033[94mPublic URL: {public_url}\033[0m")
    print("\033[93m\nSend POST requests to the Public URL with JSON data:\033[0m")
    print("\033[93m  {\"title\": \"Your Title\", \"message\": \"Your Message\"}\033[0m")
    print("\033[91mAuthorization header required: Bearer", WEBHOOK_AUTH_TOKEN, "\033[0m")
    print("\033[96m\nTest it with this curl command:\033[0m")
    print(f"\033[96m  curl -X POST {public_url} \\")
    print(f"    -H \"Authorization: Bearer {WEBHOOK_AUTH_TOKEN}\" \\")
    print("    -H \"Content-Type: application/json\" \\")
    print("    -d '{\"title\": \"Test Notification\", \"message\": \"Hello from curl!\"}'\033[0m")
    print("\033[93m\nPress Ctrl+C to exit...\033[0m")

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")

# --- Entry Point ---
if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        logger.info("Ctrl+C detected. Shutting down server...")
        tunnels = ngrok.get_tunnels()
        if tunnels:
            logger.info(f"Closing {len(tunnels)} ngrok tunnel(s)...")
            for tunnel in tunnels:
                ngrok.disconnect(tunnel.public_url)
            ngrok.kill()
            logger.info("Ngrok tunnels closed.")
        else:
            logger.info("No active ngrok tunnels found to close.")
        logger.info("PopDesk server stopped.")
        print("\n\033[92mServer shutdown complete.\033[0m")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        print("\033[91mAn unexpected error forced shutdown:", e, "\033[0m")
        try:
            ngrok.kill()
        except Exception as ng_err:
            logger.error(f"Error during ngrok cleanup on unexpected exit: {ng_err}")
        sys.exit(1)
