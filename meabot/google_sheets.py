# meabot/google_sheets.py

import os
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from django.core.cache import cache
import json
import certifi
import httplib2
import socket
from urllib3.util.ssl_ import create_urllib3_context
from google.auth.transport.requests import Request

SHEETS_CACHE_TTL = 900
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SPREADSHEET_ID = "16cHaJQiUydZtf4SCoy_g7menpb_U7Fu2qDuTLo8GH9M"
EXCHANGE_RANGE_NAME = "Exchanges!A2:G"

INTERNSHIPS_RANGE_NAME = "Internships!A2:F"

# NEW range for questions, starting row 2, columns A-D
QUESTIONS_RANGE_NAME = "Questions!A2:F"

# Build service once at startup
service = None

def _get_ssl_context():
    ctx = create_urllib3_context()
    ctx.options |= (
        0x4 << 9  # OP_NO_TLSv1
        | 0x8 << 9  # OP_NO_TLSv1_1
    )
    return ctx

def get_sheets_service():
    global service
    if not service:
        try:
            http = httplib2.Http(
                ca_certs=certifi.where(),
                ssl_context=_get_ssl_context(),
                timeout=30,
                socket_options=[
                    (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
                    (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60),
                    (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10),
                    (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
                ]
            )
            
            creds = Credentials.from_service_account_file(
                os.path.join(os.path.dirname(__file__), '../credentials.json'),
                scopes=SCOPES
            )
            creds.refresh(Request(http=http))
            
            service = build('sheets', 'v4', credentials=creds, http=http, cache_discovery=False)
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {str(e)}")
            raise
    return service

def fetch_exchange_opportunities():
    cached = cache.get('exchange_opportunities_data')
    if cached:
        return cached
        
    service = get_sheets_service()
    sheet = service.spreadsheets()
    response = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=EXCHANGE_RANGE_NAME
    ).execute()

    values = response.get('values', [])
    data = []
    for row in values:
        if len(row) < 7:
            continue
        data.append({
            'program_name': row[0],
            'partner_university': row[1],
            'who_can_apply': row[2],
            'start_reg': row[3],
            'end_reg': row[4],
            'duration': row[5],
            'website': row[6],
        })
    
    cache.set('exchange_opportunities_data', data, SHEETS_CACHE_TTL)
    return data

# NEW function to record a question
def record_user_question(user_id, username, question_text):
    """
    Appends a row to the 'Questions' tab with columns:
    Timestamp, UserID, Username, Question
    """
    service = get_sheets_service()
    sheet = service.spreadsheets()

    timestamp = datetime.datetime.now().isoformat()
    new_row = [[timestamp, user_id, username, question_text]]

    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=QUESTIONS_RANGE_NAME,
        valueInputOption="USER_ENTERED",
        body={"values": new_row}
    ).execute()


# NEW: Function to check for answers and send them via Telegram
def check_and_send_pending_answers(application):
    """
    Checks the 'Questions' sheet for rows where an answer has been provided
    (i.e. column E is nonempty) and the 'Sent' column (F) is not "yes".
    For each such row, the bot sends the answer to the user (using the UserID in column B)
    and then updates the row to mark the answer as sent.
    """
    service = get_sheets_service()
    sheet = service.spreadsheets()

    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=QUESTIONS_RANGE_NAME
    ).execute()

    rows = result.get('values', [])
    if not rows:
        print("No question rows found.")
        return

    # Import async_to_sync to call our asynchronous bot method in this synchronous context.
    from asgiref.sync import async_to_sync

    # Process each row; note that the sheet rows start at row 2.
    for i, row in enumerate(rows):
        # Ensure the row has 6 columns (fill missing ones with empty strings)
        row_extended = row + [""] * (6 - len(row))
        timestamp, user_id, username, question_text, answer_text, sent = row_extended

        # If an answer exists and it has not been sent yet...
        if answer_text.strip() and sent.strip().lower() != "yes":
            message_text = (
                "✅ *Answer Received*\n\n"
                f"*Your question:* {question_text}\n\n"
                f"*Our answer:* {answer_text}"
            )
            try:
                chat_id = int(user_id)
            except Exception as e:
                print(f"Error converting user_id {user_id} to int: {e}")
                continue

            # Send the answer to the user via Telegram.
            async_to_sync(application.bot.send_message)(
                chat_id=chat_id, text=message_text, parse_mode="Markdown"
            )
            print(f"Sent answer to user {chat_id}.")

            # Now update the sheet to mark this answer as sent.
            # The actual row number in the sheet is (i + 2)
            row_number = i + 2
            update_range = f"Questions!F{row_number}"
            body = {"values": [["yes"]]}
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=update_range,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()

def fetch_internships():
    cached = cache.get('internships_data')
    if cached:
        return cached
        
    service = get_sheets_service()
    sheet = service.spreadsheets()
    response = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=INTERNSHIPS_RANGE_NAME
    ).execute()

    values = response.get('values', [])
    data = []
    for row in values:
        if len(row) < 6:  # Ensure all 6 columns exist
            continue
        data.append({
            'internship_program': row[0],
            'field_department': row[1],
            'duration_details': row[2],
            'location': row[3],
            'application_deadline': row[4],
            'application_link': row[5],
        })
    
    cache.set('internships_data', data, SHEETS_CACHE_TTL)
    return data