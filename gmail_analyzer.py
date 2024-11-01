import os
import pickle
import re
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from prettytable import PrettyTable

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
BATCH_SIZE = 1000  # Number of emails to process per run

def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
    creds = None
    try:
        # Load existing credentials if they exist
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # If credentials are invalid, refresh or initiate OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("Error: 'credentials.json' file not found.")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return build('gmail', 'v1', credentials=creds)
    except Exception as error:
        print(f"An error occurred during Gmail service initialization: {error}")
        return None

def get_messages(service, user_id='me', page_token=None):
    """Retrieve a batch of messages from the user's Gmail account."""
    try:
        response = service.users().messages().list(userId=user_id, pageToken=page_token, maxResults=500).execute()
        messages = response.get('messages', [])
        next_page_token = response.get('nextPageToken', None)
        return messages, next_page_token
    except Exception as error:
        print(f"An error occurred while retrieving messages: {error}")
        return [], None

def analyze_message(service, user_id, msg_id):
    """Analyze a single email message and extract relevant information."""
    try:
        message = service.users().messages().get(
            userId=user_id,
            id=msg_id,
            format='metadata',
            metadataHeaders=['From', 'Subject']
        ).execute()
        headers = message.get('payload', {}).get('headers', [])
        sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown')
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
        labels = message.get('labelIds', [])
        sender_name, sender_email = extract_sender_info(sender)
        return sender_name, sender_email, subject, labels
    except Exception as error:
        print(f"An error occurred while analyzing a message: {error}")
        return None, None, None, []

def extract_sender_info(sender):
    """Extract sender name and email address from the 'From' header."""
    match = re.match(r'"?(.+?)"?\s*(?:<(.+@.+)>)?', sender)
    if match:
        sender_name = match.group(1).strip()
        sender_email = match.group(2) if match.group(2) else ''
        return sender_name, sender_email
    else:
        return sender, ''

def categorize_service(subject, labels):
    """Categorize emails based on subject keywords or Gmail labels."""
    if 'CATEGORY_PERSONAL' in labels:
        return 'Personal'
    elif 'CATEGORY_SOCIAL' in labels:
        return 'Social'
    elif 'CATEGORY_PROMOTIONS' in labels:
        return 'Promotions'
    elif 'CATEGORY_UPDATES' in labels:
        return 'Updates'
    elif 'CATEGORY_FORUMS' in labels:
        return 'Forums'
    else:
        subscription_keywords = {'subscription', 'newsletter', 'welcome', 'account'}
        if any(keyword in subject.lower() for keyword in subscription_keywords):
            return 'Subscription'
        else:
            return 'Data Holder'

def load_processed_ids():
    """Load the set of processed message IDs from a pickle file."""
    if os.path.exists('processed_ids.pickle'):
        with open('processed_ids.pickle', 'rb') as f:
            return pickle.load(f)
    else:
        return set()

def save_processed_ids(processed_ids):
    """Save the set of processed message IDs to a pickle file."""
    with open('processed_ids.pickle', 'wb') as f:
        pickle.dump(processed_ids, f)

def main():
    """Main function to process Gmail messages and categorize them."""
    service = get_gmail_service()
    if not service:
        print("Failed to initialize Gmail service.")
        return

    processed_ids = load_processed_ids()
    page_token = None
    total_processed = 0
    services = {}

    while total_processed < BATCH_SIZE:
        messages, page_token = get_messages(service, page_token=page_token)
        if not messages:
            break  # No more messages to process

        for message in messages:
            msg_id = message['id']
            if msg_id in processed_ids:
                continue  # Skip already processed messages

            sender_name, sender_email, subject, labels = analyze_message(service, 'me', msg_id)
            if sender_name:
                service_type = categorize_service(subject, labels)
                key = sender_email if sender_email else sender_name
                services.setdefault(key, {
                    'name': sender_name,
                    'email': sender_email,
                    'type': service_type,
                    'count': 0
                })
                services[key]['count'] += 1

            processed_ids.add(msg_id)
            total_processed += 1

            if total_processed >= BATCH_SIZE:
                break  # Reached the batch size limit

        if not page_token:
            break  # No more pages to fetch

    save_processed_ids(processed_ids)

    # Display the results
    table = PrettyTable()
    table.field_names = ["Service/Company Name", "Email Address", "Type", "Email Count"]
    for key, info in sorted(services.items()):
        table.add_row([info['name'], info['email'], info['type'], info['count']])
    print(table)

    # Totals per category
    type_counts = {}
    for info in services.values():
        service_type = info['type']
        type_counts[service_type] = type_counts.get(service_type, 0) + 1
    print("\nTotals per Category:")
    for service_type, count in type_counts.items():
        print(f"{service_type}: {count}")

if __name__ == '__main__':
    main()
