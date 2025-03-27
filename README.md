# 🖥️ popdesk

<p align="center">
  <img src="logo.png" alt="PopDesk Logo" width="400"/>
</p>

🚀 A simple webhook server that triggers **desktop notifications** when it receives HTTP requests. This server uses **ngrok** to expose the webhook endpoint to the internet, making it accessible from anywhere.

---

## ✨ Features

- 📬 Receive webhook notifications via HTTP POST requests  
- 🔔 Display desktop notifications with customizable **title** and **message**  
- 🌐 Expose the webhook server to the internet using **ngrok**  
- ❤️ Simple health check endpoint via GET requests  
- 🔐 Secure endpoints with **authorization headers**  
- ⚡ Powered by **FastAPI** for performance & built-in docs  

---

## 📦 Requirements

- 🐍 Python 3.6+  
- 🪟 Windows OS (notifications currently Windows-specific)

---

## ⚙️ Setup

```bash
git clone https://github.com/tsilva/popdesk.git
cd popdesk
chmod +x install.sh
./install.sh
source venv/bin/activate
```

🛠️ The install script will:
1. 🧪 Create (or use) a Python virtual environment  
2. 📦 Install dependencies from `requirements.txt`  
3. 📝 Create a `.env` file from `.env.example` (if missing)

⚠️ **Note:** Manually activate the virtual environment after install.

---

### 🔧 Update Your `.env` File

- 🔐 `WEBHOOK_AUTH_TOKEN` → Set a secure token to protect your webhook  
- 🔢 `WEBHOOK_PORT` → Optional, defaults to `8000`
- 🌐 `NGROK_AUTH_TOKEN` → Your ngrok token (if using ngrok)  

---

### 🌍 Setting Up ngrok (Optional)

1. 📝 [Sign up](https://ngrok.com) for an ngrok account  
2. 🔑 Copy your authtoken from your ngrok dashboard  
3. ⚙️ Add it to the `.env` file under `NGROK_AUTH_TOKEN`

---

## 🚀 Usage

### ▶️ Start the Server

```bash
python main.py
```

The server will:
- 🛡️ Start on `localhost:8000` or your chosen port  
- 🌐 Create an **ngrok tunnel** and show the public URL  
- ⏳ Run until you press `Ctrl + C` to stop

---

### 📣 Sending Notifications

You can trigger a notification via a POST request. Example using `curl`:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_webhook_auth_token" \
  -d '{"title": "Test Notification", "message": "Hello from the webhook!"}' \
  <your-ngrok-url>
```

---

### 📚 API Documentation

Thanks to FastAPI, you get automatic interactive docs:

- 📄 Swagger UI: `http://localhost:{PORT}/docs`  
- 📘 ReDoc: `http://localhost:{PORT}/redoc`

---

## 💡 How it Works

1. 🌐 Server listens for `POST` requests with JSON payload  
2. 🔐 Validates requests with the `Authorization` header  
3. 🪟 Triggers a **Windows notification** using PowerShell  
4. 🧭 Ngrok tunnels your local server for external access  

---

## 🧰 Troubleshooting

- ❌ No notification? → Ensure you're on **Windows** and check notification settings  
- 🌐 ngrok issues? → Check your internet & token setup  
- 🛑 401 Unauthorized? → Validate your `Authorization` header  
- 🐛 Still stuck? → Watch console logs & check `/docs` or `/redoc`  

---

## 📄 License

📝 [MIT License](LICENSE)