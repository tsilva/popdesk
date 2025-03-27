import os
import sys
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException, status
from pydantic import BaseModel
import pyngrok.ngrok as ngrok
from plyer import notification
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Early validation of environment variables
def validate_env_vars():
    # Define default placeholder values to check for
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

    # Optional: Validate PORT format
    port_str = os.getenv('PORT', '8000') # Get PORT or default
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

# Validate environment variables before proceeding
validate_env_vars()

# --- Define request model ---
class NotificationPayload(BaseModel):
    title: Optional[str] = "Webhook Notification"
    message: Optional[str] = "You received a webhook notification!"

# --- Initialize FastAPI and environment variables ---
app = FastAPI(
    title="PopDesk",
    description="A webhook server that triggers desktop notifications",
    version="1.0.0"
)

# Read validated environment variables
PORT = int(os.getenv('PORT', 8000)) # Default needed if PORT check is removed from validation
NGROK_AUTH_TOKEN = os.getenv('NGROK_AUTH_TOKEN')
WEBHOOK_AUTH_TOKEN = os.getenv('WEBHOOK_AUTH_TOKEN') # Standardized variable

# --- Set up ngrok ---
# Check if NGROK_AUTH_TOKEN is actually set before using it
if NGROK_AUTH_TOKEN:
    try:
        ngrok.set_auth_token(NGROK_AUTH_TOKEN)
        logger.info("Ngrok auth token set.")
    except Exception as e:
        logger.error(f"Failed to set ngrok auth token: {e}. Tunnel might fail if token is required.")
        # Decide if this is critical - potentially exit or just warn
        # sys.exit(1) # Uncomment to make a valid ngrok token mandatory
else:
    # This case should ideally be caught by validate_env_vars if NGROK_AUTH_TOKEN is mandatory
    logger.warning("NGROK_AUTH_TOKEN is not set. Ngrok connection might be limited or fail.")


# --- Authentication dependency ---
async def verify_auth_header(request: Request):
    auth_header = request.headers.get('Authorization')
    # Compare against the standardized WEBHOOK_AUTH_TOKEN
    if not auth_header or not auth_header.startswith('Bearer ') or auth_header.split(' ')[1] != WEBHOOK_AUTH_TOKEN:
        logger.warning(f"Unauthorized access attempt from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Optional: Log successful authentication if needed
    # logger.info(f"Authorized request received from {request.client.host}")
    return True

# --- API Endpoints ---
@app.get("/", status_code=200)
async def health_check():
    """Provides a simple health check endpoint."""
    return {"status": "healthy", "message": "PopDesk webhook server is running"}

@app.post("/", status_code=200)
async def webhook(payload: NotificationPayload, authorized: bool = Depends(verify_auth_header)):
    """
    Receives webhook notifications via POST request, validates authentication,
    and triggers a desktop notification.
    """
    if not authorized:
        # This check is technically redundant because Depends raises HTTPException,
        # but it makes the control flow explicit.
        return # Should not be reached if Depends works correctly

    try:
        # Display notification using plyer
        notification.notify(
            title=payload.title or "Webhook Notification", # Use default if None
            message=payload.message or "You received a webhook notification!", # Use default if None
            app_name="PopDesk",
            timeout=10 # Duration notification stays on screen (in seconds)
        )

        logger.info(f"Notification displayed: Title='{payload.title}'")
        return {"status": "success", "message": "Notification sent"}

    except NotImplementedError as nie:
        # Specific error if plyer doesn't support notifications on the current OS/setup
        logger.error(f"Plyer notification feature not implemented or supported on this system: {str(nie)}")
        raise HTTPException(status_code=501, detail=f"Notifications not supported on this system: {str(nie)}")
    except Exception as e:
        # Catch other potential errors during notification display
        logger.error(f"Error processing or displaying notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error processing notification: {str(e)}")

# --- Server Start Logic ---
def start():
    """Sets up the ngrok tunnel and starts the Uvicorn server."""
    public_url = None
    try:
        # Create an HTTP tunnel on the specified port
        logger.info(f"Attempting to establish ngrok tunnel on port {PORT}...")
        http_tunnel = ngrok.connect(PORT)
        public_url = http_tunnel.public_url
        logger.info(f"Ngrok tunnel established successfully at: {public_url}")

    except Exception as e:
        logger.error(f"FATAL: Failed to establish ngrok tunnel: {e}")
        print("\033[91m" + f"Error: Could not start ngrok tunnel." + "\033[0m")
        print("\033[93m" + f"  Reason: {e}" + "\033[0m")
        print("\033[93m" + "  Please check:" + "\033[0m")
        print("\033[93m" + "  - Your NGROK_AUTH_TOKEN in the .env file is correct (if required)." + "\033[0m")
        print("\033[93m" + "  - Your internet connection." + "\033[0m")
        print("\033[93m" + "  - That no other ngrok instance is conflicting on this port." + "\033[0m")
        sys.exit(1) # Exit if ngrok fails critically

    # Proceed only if tunnel setup was successful
    logger.info(f"Starting PopDesk webhook server on http://0.0.0.0:{PORT}")
    print("\033[92m" + f"\nPopDesk Webhook Server is RUNNING!" + "\033[0m")
    print("\033[94m" + f"Local URL:  http://localhost:{PORT}" + "\033[0m")
    print("\033[94m" + f"Public URL: {public_url}" + "\033[0m")
    print("\033[93m" + "\nSend POST requests to the Public URL with JSON data:" + "\033[0m")
    print("\033[93m" + '  {"title": "Your Title", "message": "Your Message"}' + "\033[0m")
    print("\033[91m" + f"Include the Authorization header: Bearer {WEBHOOK_AUTH_TOKEN}" + "\033[0m")
    # Add sample curl command
    print("\033[96m" + "\nTest it with this curl command:" + "\033[0m")
    print("\033[96m" + f"  curl -X POST {public_url} \\" + "\033[0m")
    print("\033[96m" + f"    -H \"Authorization: Bearer {WEBHOOK_AUTH_TOKEN}\" \\" + "\033[0m")
    print("\033[96m" + "    -H \"Content-Type: application/json\" \\" + "\033[0m")
    print("\033[96m" + "    -d '{\"title\": \"Test Notification\", \"message\": \"Hello from curl!\"}'" + "\033[0m")
    print("\033[93m" + "\nPress Ctrl+C to exit..." + "\033[0m")

    # Configure Uvicorn to run with graceful shutdown handled by the main block
    # Use reload=False for production/stable running
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info") # Match logging level

# --- Main Execution Block ---
if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        logger.info("Ctrl+C detected. Shutting down server...")
        # Clean up ngrok tunnels gracefully
        tunnels = ngrok.get_tunnels()
        if tunnels:
            logger.info(f"Closing {len(tunnels)} ngrok tunnel(s)...")
            for tunnel in tunnels:
                 ngrok.disconnect(tunnel.public_url)
            ngrok.kill() # Ensure ngrok process is terminated
            logger.info("Ngrok tunnels closed.")
        else:
             logger.info("No active ngrok tunnels found to close.")
        logger.info("PopDesk server stopped.")
        print("\n\033[92m" + "Server shutdown complete." + "\033[0m")
        sys.exit(0)
    except Exception as e:
        # Catch unexpected errors during startup or runtime not caught elsewhere
        logger.exception(f"An unexpected error occurred: {e}") # Use logger.exception to include traceback
        print("\033[91m" + f"An unexpected error forced shutdown: {e}" + "\033[0m")
        try:
            # Attempt to kill ngrok even on unexpected exit
            ngrok.kill()
        except Exception as ng_err:
            logger.error(f"Error during ngrok cleanup on unexpected exit: {ng_err}")
        sys.exit(1)