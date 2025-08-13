Email Reply Agent
This project implements an automated email reply agent using Python, LangGraph, and the Gemini 1.5 Flash API. The agent polls your Gmail inbox for new, unread emails, assesses whether a reply is needed, generates a professional response if necessary, and sends it back in the same email thread. The system is designed to run continuously, checking for new emails every 60 seconds.
Features

Email Polling: Checks Gmail inbox for unread emails from others (excludes emails sent by you).
Reply Assessment: Uses Gemini 1.5 Flash to determine if an email requires a response.
Automated Replies: Generates professional, business-casual replies using Gemini 1.5 Flash.
Threaded Responses: Sends replies in the same email thread for context.
Mark as Read: Marks processed emails as read to avoid reprocessing.
Continuous Operation: Runs in a loop, polling every 60 seconds.

Prerequisites

Python 3.8+
Google Cloud Project with Gmail API enabled and OAuth 2.0 credentials.
Gemini API Key from Google AI Studio.
Dependencies:
langgraph
langchain
langchain-google-genai
google-api-python-client
google-auth-oauthlib
google-auth-httplib2



Installation

Clone the Repository:
git clone <repository-url>
cd email-reply-agent


Install Dependencies:
pip install langgraph langchain langchain-google-genai google-api-python-client google-auth-oauthlib google-auth-httplib2


Set Up Gmail API:

Go to Google Cloud Console.
Create a project and enable the Gmail API.
Create OAuth 2.0 credentials (Desktop app).
Download the credentials.json file and place it in the project directory.
Ensure the OAuth consent screen includes the https://www.googleapis.com/auth/gmail.modify and https://www.googleapis.com/auth/gmail.send scopes.


Set Up Gemini API:

Obtain a Gemini API key from Google AI Studio.
Replace YOUR_GEMINI_API_KEY in the script with your actual API key.



Usage

Prepare the Script:

Ensure credentials.json is in the project directory.
Update the GOOGLE_API_KEY environment variable in the script with your Gemini API key:os.environ["GOOGLE_API_KEY"] = "your-actual-gemini-api-key"




Run the Agent:
python email_reply_agent.py


On first run, the script will prompt you to authenticate via OAuth, opening a browser to log in to your Google account.
A token.json file will be created to store authentication credentials for subsequent runs.


Operation:

The agent checks your Gmail inbox every 60 seconds for unread emails.
For each email, it uses Gemini 1.5 Flash to determine if a reply is needed.
If a reply is needed, it generates a professional response and sends it in the same thread.
Processed emails are marked as read.



Customization

Reply Tone: Modify the SystemMessage in the generate_reply function to adjust the tone or style of responses (e.g., formal, friendly).
Polling Interval: Change time.sleep(60) to adjust how often the inbox is checked.
Email Filters: Update the Gmail query in fetch_emails (e.g., q='is:unread -from:me') to filter specific emails (e.g., by sender or label).
Draft Instead of Send: Modify the send_reply function to create drafts instead of sending replies by replacing messages().send() with messages().drafts().create().

Notes

Ensure your Gmail API credentials have the correct scopes (modify and send).
The script processes up to 5 emails per cycle to avoid rate limits; adjust in fetch_emails if needed.
If errors occur (e.g., rate limits, authentication issues), they are printed to the console, and the agent continues running.
The agent assumes "Gemini 2.5 Flash" is a typo for "Gemini 1.5 Flash". Update the model in ChatGoogleGenerativeAI if a different model is intended.

Troubleshooting

Authentication Errors: Ensure credentials.json is valid and the OAuth consent screen is configured correctly.
Gemini API Errors: Verify your API key and ensure you have sufficient quota.
No Emails Processed: Check the Gmail query in fetch_emails and ensure emails match the criteria (e.g., is:unread).
Rate Limits: Reduce the number of emails processed per cycle or increase the sleep interval.

License
This project is licensed under the MIT License.
