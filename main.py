#!/usr/bin/env python3

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from plyer import notification
from pyngrok import ngrok
import threading
import sys

# Configuration
WEBHOOK_AUTH_TOKEN = os.env["WEBHOOK_AUTH_TOKEN"]
PORT = int(os.getenv("PORT", 8000))

# Webhook handler class
class NotificationHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Check for the Authorization header
        auth_header = self.headers.get('Authorization')
        if not auth_header or auth_header != f"Bearer {WEBHOOK_AUTH_TOKEN}":
            # Unauthorized response
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Unauthorized"}).encode('utf-8'))
            return
        
        # Read and parse the incoming POST data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            title = data.get('title', 'Notification')
            message = data.get('message', 'No message provided')
            
            # Trigger desktop notification
            notification.notify(
                title=title,
                message=message,
                app_name="WebhookNotifier",
                timeout=10
            )
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": "Notification sent"}).encode('utf-8'))
        
        except json.JSONDecodeError:
            # Handle invalid JSON
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Invalid JSON"}).encode('utf-8'))

    def do_GET(self):
        # Simple health check endpoint (no auth required for simplicity)
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Webhook server is running!")

# Function to start the HTTP server
def start_server(port=PORT):
    server_address = ('', port)
    httpd = HTTPServer(server_address, NotificationHandler)
    print(f"Starting webhook server on port {port}...")
    httpd.serve_forever()

# Main function to set up ngrok and run the server
def main():
    # Start the HTTP server in a separate thread
    server_thread = threading.Thread(target=start_server, args=(PORT,))
    server_thread.daemon = True  # Allows the script to exit cleanly
    server_thread.start()
    
    # Set up ngrok tunnel
    try:
        # Uncomment and replace with your ngrok authtoken if not configured globally
        # ngrok.set_auth_token('YOUR_AUTH_TOKEN')
        
        public_url = ngrok.connect(PORT, "http").public_url
        print(f"Webhook exposed at: {public_url}")
        print(f"Send a POST request to {public_url} with JSON like:")
        print('{"title": "Test", "message": "Hello from the webhook!"}')
        print(f"Include header: Authorization: Bearer {WEBHOOK_AUTH_TOKEN}")
        
        # Keep the script running
        input("Press Enter to exit...\n")
        
    except Exception as e:
        print(f"Error setting up ngrok: {e}")
        sys.exit(1)
    
    # Cleanup on exit
    ngrok.disconnect(public_url)
    ngrok.kill()

if __name__ == "__main__":
    main()