import os
import json
import requests
from flask import Flask, request
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Configuration
os.environ["GOOGLE_API_KEY"] = "YOUR_GEMINI_API_KEY"  # Replace with your Gemini API key
META_ACCESS_TOKEN = "YOUR_META_ACCESS_TOKEN"  # From Meta App Dashboard
PHONE_NUMBER_ID = "YOUR_PHONE_NUMBER_ID"  # From Meta App Dashboard
VERIFY_TOKEN = "YOUR_VERIFY_TOKEN"  # Choose a secure string
VERSION = "v18.0"  # Meta Graph API version

# Initialize Flask app and Gemini
app = Flask(__name__)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Webhook verification endpoint
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    if (
        request.args.get("hub.mode") == "subscribe"
        and request.args.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return request.args.get("hub.challenge"), 200
    return "Verification failed", 403

# Webhook endpoint to receive messages
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data or "object" not in data or "entry" not in data:
        return "", 200

    for entry in data["entry"]:
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue
            for message in change["value"].get("messages", []):
                if message["type"] != "text":
                    continue
                sender = message["from"]
                message_text = message["text"]["body"]
                message_id = message["id"]

                # Assess if reply is needed
                needs_reply = assess_reply(message_text)
                if not needs_reply:
                    continue

                # Generate reply
                reply = generate_reply(message_text)
                if reply:
                    send_reply(sender, reply, message_id)
    return "", 200

def assess_reply(message_text: str) -> bool:
    prompt = SystemMessage(content="Determine if this WhatsApp message needs a reply. Output JSON: {'needs_reply': true/false}")
    user_msg = HumanMessage(content=f"Message: {message_text}")
    try:
        response = llm.invoke([prompt, user_msg])
        result = json.loads(response.content)
        return result.get("needs_reply", False)
    except:
        return False

def generate_reply(message_text: str) -> str:
    prompt = SystemMessage(content="""You are a helpful assistant drafting WhatsApp replies.
    Use a friendly, professional tone. Keep replies concise, under 200 characters if possible.
    Output plain text. If the message is a question, answer it or use '[YOUR_ANSWER_HERE]' if unknown.""")
    user_msg = HumanMessage(content=f"Message: {message_text}")
    try:
        response = llm.invoke([prompt, user_msg])
        return response.content.strip()
    except:
        return "Thanks for your message! I'll get back to you soon."

def send_reply(recipient: str, message: str, reply_to_id: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message},
        "context": {"message_id": reply_to_id},
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send reply: {e}")

if __name__ == "__main__":
    app.run(port=8000)
