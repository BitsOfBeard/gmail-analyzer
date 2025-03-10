import os
import pickle
import re
import csv
import argparse
from datetime import datetime
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import email.utils

# Configuration constants
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
BATCH_SIZE = 1000
CSV_FILENAME = 'email_analysis.csv'

PICKLE_FILENAME = 'processed_ids.pickle'

def get_gmail_service():
    """Authenticate and return Gmail API service instance."""
    creds = None
    try:
        if os.path.exists('gmail_token.pickle'):
            with open('gmail_token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError("'credentials.json' file not found.")
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('gmail_token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return build('gmail', 'v1', credentials=creds)
    except Exception as error:
        print(f"Authentication error: {error}")
        return None

def get_messages(service, user_id='me', page_token=None):
    """Retrieve a batch of messages from Gmail."""
    try:
        response = service.users().messages().list(
            userId=user_id,
            pageToken=page_token,
            maxResults=500
        ).execute()
        return response.get('messages', []), response.get('nextPageToken')
    except Exception as error:
        print(f"Error retrieving messages: {error}")
        return [], None

def analyze_message(service, user_id, msg_id):
    """Analyze a single email message's metadata."""
    try:
        message = service.users().messages().get(
            userId=user_id,
            id=msg_id,
            format='metadata',
            metadataHeaders=['From']
        ).execute()

        headers = message.get('payload', {}).get('headers', [])
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')

        sender_name, sender_email = extract_sender_info(sender)
        return sender_name, sender_email, sender
    except Exception as error:
        print(f"Error analyzing message {msg_id}: {error}")
        return None, None, None

def extract_sender_info(sender):
    """Extract sender name and email using email.utils.parseaddr."""
    name, email_address = email.utils.parseaddr(sender)
    name = name.strip() if name else None

    # Validate email
    email_regex = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', re.IGNORECASE)
    valid_email = None
    if email_address:
        email_address = email_address.strip().lower()
        if email_regex.match(email_address):
            valid_email = email_address
    return name, valid_email

def load_processed_data():
    """Load both processed IDs and CSV data with integrity checks."""
    processed_ids = set()
    csv_data = {}

    # Load processed IDs
    if Path(PICKLE_FILENAME).exists():
        try:
            with open(PICKLE_FILENAME, 'rb') as f:
                processed_ids = pickle.load(f)
                if not isinstance(processed_ids, set):
                    raise ValueError("Invalid processed IDs format")
        except (EOFError, pickle.UnpicklingError) as e:
            print(f"Corrupted {PICKLE_FILENAME}, resetting...")
            processed_ids = set()

    # Load CSV data
    if Path(CSV_FILENAME).exists():
        try:
            with open(CSV_FILENAME, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = (row['Email Address'].strip().lower(), row['Service/Company Name'].strip().lower())
                    csv_data[key] = {
                        'count': int(row['count']),
                        'first_seen': row.get('first_seen', datetime.now().isoformat()),
                        'last_seen': row.get('last_seen', datetime.now().isoformat())
                    }
        except (csv.Error, KeyError) as e:
            print(f"Corrupted {CSV_FILENAME}, resetting...")
            csv_data = {}

    return processed_ids, csv_data

def save_data(processed_ids, csv_data):
    """Atomic save operations for both data stores."""
    # Save processed IDs
    temp_pickle = f"{PICKLE_FILENAME}.tmp"
    with open(temp_pickle, 'wb') as f:
        pickle.dump(processed_ids, f)
    os.replace(temp_pickle, PICKLE_FILENAME)

    # Save CSV data
    temp_csv = f"{CSV_FILENAME}.tmp"
    with open(temp_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Service/Company Name', 
            'Email Address', 
            'count',
            'first_seen',
            'last_seen'
        ])
        writer.writeheader()
        for (email, name), data in csv_data.items():
            writer.writerow({
                'Service/Company Name': name,
                'Email Address': email,
                'count': data['count'],
                'first_seen': data['first_seen'],
                'last_seen': data['last_seen']
            })
    os.replace(temp_csv, CSV_FILENAME)

def update_csv_data(csv_data, sender_name, sender_email):
    """Update CSV data with new entry."""
    current_time = datetime.now().isoformat()
    key = (sender_email.strip().lower(), sender_name.strip().lower() if sender_name else "Unknown")

    if key in csv_data:
        csv_data[key]['count'] += 1
        csv_data[key]['last_seen'] = current_time
    else:
        csv_data[key] = {
            'count': 1,
            'first_seen': current_time,
            'last_seen': current_time
        }
    return csv_data

def main():
    parser = argparse.ArgumentParser(description='Gmail Account Analyzer')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                       help='Number of emails to process per run')
    parser.add_argument('--export-only', action='store_true',
                       help='Export existing CSV without processing')
    args = parser.parse_args()

    processed_ids, csv_data = load_processed_data()

    if args.export_only:
        print(f"Current CSV contains {len(csv_data)} entries")
        return

    service = get_gmail_service()
    if not service:
        return

    total_processed = 0
    page_token = None

    try:
        while total_processed < args.batch_size:
            messages, page_token = get_messages(service, page_token=page_token)
            if not messages:
                break

            for message in messages:
                if total_processed >= args.batch_size:
                    break

                msg_id = message['id']
                if msg_id in processed_ids:
                    continue

                sender_name, sender_email, sender_header = analyze_message(service, 'me', msg_id)
                reason = []
                if not sender_email:
                    reason.append('missing email')

                # Track emails based on email address
                if sender_email:
                    csv_data = update_csv_data(csv_data, sender_name, sender_email)

                processed_ids.add(msg_id)
                total_processed += 1

            if not page_token:
                break

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    finally:
        save_data(processed_ids, csv_data)
        print(f"Processed {total_processed} new emails. Total unique senders: {len(csv_data)}")

if __name__ == '__main__':
    main()
