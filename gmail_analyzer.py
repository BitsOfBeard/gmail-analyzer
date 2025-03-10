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
from prettytable import PrettyTable

# Configuration constants
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
BATCH_SIZE = 10000
CSV_FILENAME = 'email_analysis.csv'

PICKLE_FILENAME = 'processed_ids.pickle'

# Update these constants at the top
CREDENTIALS_PICKLE = 'gmail_token.pickle'  # Separate file for auth credentials
PROCESSED_IDS_PICKLE = 'processed_ids.pickle'  # Only for message IDs


def get_gmail_service():
    """Authenticate and return Gmail API service instance."""
    creds = None
    try:
        if os.path.exists(CREDENTIALS_PICKLE):
            with open(CREDENTIALS_PICKLE, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError("'credentials.json' file not found.")
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open(CREDENTIALS_PICKLE, 'wb') as token:
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
            metadataHeaders=['From', 'Subject']
        ).execute()

        headers = message.get('payload', {}).get('headers', [])
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        labels = message.get('labelIds', [])

        sender_name, sender_email = extract_sender_info(sender)
        return sender_name, sender_email, subject, labels
    except Exception as error:
        print(f"Error analyzing message {msg_id}: {error}")
        return None, None, None, []

def extract_sender_info(sender):
    """Extract sender name and email from From header."""
    email_match = re.search(r'<?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)>?', sender)
    name_match = re.search(r'^"?([^"<]+)"?\s*<', sender)

    sender_email = email_match.group(1) if email_match else ''
    sender_name = name_match.group(1).strip() if name_match else sender.replace(sender_email, '').strip(' <>')

    return sender_name, sender_email

def categorize_service(subject, labels):
    """Categorize emails using Gmail labels and subject analysis."""
    label_map = {
        'CATEGORY_PERSONAL': 'Personal',
        'CATEGORY_SOCIAL': 'Social',
        'CATEGORY_PROMOTIONS': 'Promotions',
        'CATEGORY_UPDATES': 'Updates',
        'CATEGORY_FORUMS': 'Forums'
    }

    for label, category in label_map.items():
        if label in labels:
            return category

    subscription_keywords = {'subscription', 'newsletter', 'welcome', 'account'}
    if any(keyword in subject.lower() for keyword in subscription_keywords):
        return 'Subscription'

    return 'Data Holder'

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
                    key = (row['Email Address'].strip(), row['Service/Company Name'].strip())
                    csv_data[key] = {
                        'count': int(row['count']),
                        'type': row['Type'],
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
            'Type', 
            'count',
            'first_seen',
            'last_seen'
        ])
        writer.writeheader()
        for (email, name), data in csv_data.items():
            writer.writerow({
                'Service/Company Name': name,
                'Email Address': email,
                'Type': data['type'],
                'count': data['count'],
                'first_seen': data['first_seen'],
                'last_seen': data['last_seen']
            })
    os.replace(temp_csv, CSV_FILENAME)

def update_csv_data(csv_data, sender_name, sender_email, service_type):
    """Update CSV data with new entry."""
    current_time = datetime.now().isoformat()
    key = (sender_email.strip().lower(), sender_name.strip())

    if key in csv_data:
        csv_data[key]['count'] += 1
        csv_data[key]['last_seen'] = current_time
        if csv_data[key]['type'] != service_type:
            csv_data[key]['type'] = f"{csv_data[key]['type']}|{service_type}"
    else:
        csv_data[key] = {
            'count': 1,
            'type': service_type,
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

                sender_name, sender_email, subject, labels = analyze_message(service, 'me', msg_id)
                if sender_name:
                    service_type = categorize_service(subject, labels)
                    csv_data = update_csv_data(csv_data, sender_name, sender_email, service_type)

                processed_ids.add(msg_id)
                total_processed += 1

            if not page_token:
                break

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    finally:
        save_data(processed_ids, csv_data)
        print(f"Processed {total_processed} new emails. Total tracked: {len(csv_data)}")

if __name__ == '__main__':
    main()
