# WhatsApp Auto-Reply Agent

This project implements an **automated WhatsApp reply agent** using **Python**, **Flask**, and the **Gemini 1.5 Flash API**.  
The agent listens for incoming WhatsApp messages via **Meta Cloud API webhooks**, assesses whether a reply is needed using Gemini, generates a **friendly and professional response**, and sends it back in the same chat thread.  
It is designed for **real-time text message processing**.

---

## 🚀 Features

- **Webhook-Based Listening** – Receives WhatsApp messages via Meta Cloud API webhooks.
- **Reply Assessment** – Uses Gemini 1.5 Flash to determine if a message requires a response.
- **Automated Replies** – Generates concise, professional replies (under 200 characters when possible).
- **Threaded Responses** – Sends replies in the same chat thread for context.
- **Real-Time Processing** – Responds instantly to incoming messages.

---

## 📋 Prerequisites

- Python **3.8+**
- **Meta Developer Account** with a WhatsApp Business App
- **Gemini API Key** from Google AI Studio
- **ngrok** for local webhook testing *(or a cloud hosting service for production)*

**Dependencies:**
```bash
pip install flask langchain langchain-google-genai requests
```

## 🛠 Installation
1️⃣ Clone the Repository
bash
Copy
Edit
git clone <repository-url>
cd whatsapp-reply-agent
2️⃣ Install Dependencies
```bash
Copy
Edit
pip install flask langchain langchain-google-genai requests\
```
## ⚙️ Setup
1. Meta WhatsApp API
- Create a Meta App at developers.facebook.com.
- Enable WhatsApp and obtain:
- META_ACCESS_TOKEN
- PHONE_NUMBER_ID
- Set up a test WhatsApp number in the dashboard.

2. Gemini API
- Get a Gemini API key from Google AI Studio.
- Update the API key in whatsapp_reply_agent.py:
```python
Copy
Edit
os.environ["GOOGLE_API_KEY"] = "your-actual-gemini-api-key"
```

3. Webhook Configuration
- Install ngrok:
```bash
Copy
Edit
ngrok http 8000
```

- Copy the public URL (e.g., https://your-ngrok-url.ngrok-free.app).
- In the Meta App Dashboard:
     * Go to WhatsApp → Configuration
     * Set the Callback URL to:

```arduino
Copy
Edit
https://your-ngrok-url.ngrok-free.app/webhook
```

- Set VERIFY_TOKEN in whatsapp_reply_agent.py:
```python
Copy
Edit
VERIFY_TOKEN = "your-secure-verify-token"
```

- Subscribe to the "messages" webhook field.

4. Update Script Placeholders
- In whatsapp_reply_agent.py, replace:

```
Copy
Edit
YOUR_GEMINI_API_KEY
YOUR_META_ACCESS_TOKEN
YOUR_PHONE_NUMBER_ID
YOUR_VERIFY_TOKEN
```

## ▶ Usage
Run the agent:

```bash
Copy
Edit
python whatsapp_reply_agent.py
```

Ensure ngrok is running in another terminal.

## 💬 Testing the Bot:
- Send a text message to your WhatsApp test number (from the Meta App Dashboard).

- The agent:

    * Assesses if a reply is needed.
    * Generates a response using Gemini 1.5 Flash.
    * Sends it back in the chat thread.
    * Check the terminal for any errors.

## 🎨 Customization
- **Reply Tone:** Modify the SystemMessage in generate_reply to adjust tone (casual, formal, etc.) or length.

- **Message Filters**: Edit assess_reply to filter messages by keywords or sender.

- **Non-Text Messages**: Extend webhook to handle other types (e.g., images) by checking message["type"].

- **Draft Storage**: Save generated replies to a database or file for manual review.

- **Production Hosting:** Deploy on Heroku, AWS, or similar instead of using ngrok.

## 📌 Notes
- Uses Meta Cloud API for reliable WhatsApp integration (avoids unofficial libraries that risk bans).

- WhatsApp requires user-initiated contact before bot replies (unless using template messages).

- If “Gemini 2.5 Flash” appears, update it to Gemini 1.5 Flash in ChatGoogleGenerativeAI.

- Webhooks need a public URL – use ngrok for local testing.

## 🐛 Troubleshooting
 Issue	Possible Fix
- Webhook Not Triggering	Verify ngrok is running and Callback URL is correct in Meta Dashboard.
- API Errors	Check META_ACCESS_TOKEN, PHONE_NUMBER_ID, and Gemini API key. Ensure API quota.
- No Replies Sent	Confirm sender has messaged bot first. Check assess_reply logic.
- Rate Limits	Monitor Meta & Gemini API usage in dashboards.

📄 License
MIT License
