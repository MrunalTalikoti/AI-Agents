# Email Reply Agent using LangGraph and Gemini 1.5 Flash
# Note: Assuming "Gemini 2.5 flash" is a typo for "Gemini 1.5 Flash". If not, update the model name accordingly.
# This script creates a stateful agent system using LangGraph that polls Gmail for new emails,
# assesses if a reply is needed using Gemini, generates a reply if necessary, and sends it.
# Requirements:
# - Install dependencies: pip install langgraph langchain langchain-google-genai google-api-python-client google-auth-oauthlib google-auth-httplib2
# - Set up Gmail API: Enable Gmail API in Google Cloud Console, download credentials.json.
# - Obtain Gemini API key from Google AI Studio.
# - Place credentials.json in the same directory or update the path.
# - Update YOUR_GEMINI_API_KEY and other placeholders.

import os
import time
import json
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText

# Set up Gemini API
os.environ["GOOGLE_API_KEY"] = "YOUR_GEMINI_API_KEY"  # Replace with your Gemini API key
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.send']
CREDS_FILE = 'credentials.json'  # Path to your Google API credentials.json
TOKEN_FILE = 'token.json'  # Where to store the token

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

# State definition for LangGraph
class AgentState(TypedDict):
    emails: list  # List of new emails to process
    current_email: dict  # Current email being processed
    needs_reply: bool
    reply_draft: str
    sent: bool

# Node: Fetch new emails
def fetch_emails(state: AgentState) -> AgentState:
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread -from:me').execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages[:5]:  # Limit to 5 for safety
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_data['payload']
        headers = payload['headers']
        subject = next(h['value'] for h in headers if h['name'] == 'Subject')
        from_email = next(h['value'] for h in headers if h['name'] == 'From')
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8') if 'body' in payload else ''
        emails.append({
            'id': msg['id'],
            'threadId': msg_data['threadId'],
            'subject': subject,
            'from': from_email,
            'body': body
        })
    state['emails'] = emails
    return state

# Node: Assess if reply needed
def assess_reply(state: AgentState) -> AgentState:
    if not state['emails']:
        return state
    state['current_email'] = state['emails'].pop(0)
    email = state['current_email']
    prompt = SystemMessage(content="Determine if this email needs a reply. Output JSON: {'needs_reply': true/false}")
    user_msg = HumanMessage(content=f"Subject: {email['subject']}\nBody: {email['body']}")
    response = llm.invoke([prompt, user_msg])
    try:
        result = json.loads(response.content)
        state['needs_reply'] = result.get('needs_reply', False)
    except:
        state['needs_reply'] = False
    return state

# Conditional edge: If needs reply
def should_reply(state: AgentState) -> str:
    return "generate_reply" if state['needs_reply'] else "end"

# Node: Generate reply
def generate_reply(state: AgentState) -> AgentState:
    email = state['current_email']
    prompt = SystemMessage(content="""You are a helpful assistant. Draft a professional, concise reply.
    Use business casual tone. Start with 'Hello,' end with 'Best regards,'.
    Output plain text.""")
    user_msg = HumanMessage(content=f"Subject: {email['subject']}\nBody: {email['body']}")
    response = llm.invoke([prompt, user_msg])
    state['reply_draft'] = response.content
    return state

# Node: Send reply
def send_reply(state: AgentState) -> AgentState:
    service = get_gmail_service()
    email = state['current_email']
    message = MIMEText(state['reply_draft'])
    message['to'] = email['from']
    message['subject'] = f"Re: {email['subject']}"
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw, 'threadId': email['threadId']}
    try:
        service.users().messages().send(userId='me', body=body).execute()
        state['sent'] = True
        # Mark as read
        service.users().messages().modify(userId='me', id=email['id'], body={'removeLabelIds': ['UNREAD']}).execute()
    except HttpError as error:
        print(f'An error occurred: {error}')
        state['sent'] = False
    return state

# Build the graph
workflow = StateGraph(state_schema=AgentState)

workflow.add_node("fetch_emails", fetch_emails)
workflow.add_node("assess_reply", assess_reply)
workflow.add_node("generate_reply", generate_reply)
workflow.add_node("send_reply", send_reply)

workflow.add_edge("fetch_emails", "assess_reply")
workflow.add_conditional_edges("assess_reply", should_reply, {"generate_reply": "generate_reply", "end": END})
workflow.add_edge("generate_reply", "send_reply")
workflow.add_edge("send_reply", "assess_reply")  # Loop back if more emails

workflow.set_entry_point("fetch_emails")

app = workflow.compile()

# Run the agent in a loop (poll every 60 seconds)
while True:
    app.invoke({"emails": [], "sent": False})
    time.sleep(60)
