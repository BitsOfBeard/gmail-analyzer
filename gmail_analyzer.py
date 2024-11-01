import os
import pickle
import re
import time
from datetime import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from prettytable import PrettyTable

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
BATCH_SIZE = 1000  # Number of emails to process per run

def get_gmail_service():
    # ... [Same as before] ...
    pass

def get_messages(service, user_id='me', page_token=None):
    try:
        response = service.users().messages().list(userId=user_id, pageToken=page_token, maxResults=500).execute()
        messages = response.get('messages', [])
        next_page_token = response.get('nextPageToken', None)
        return messages, next_page_token
    except Exception as error:
        print(f'An error occurred: {error}')
        return [], None

def analyze_message(service, user_id, msg_id):
    # ... [Same as before] ...
    pass

def extract_sender_info(sender):
    # ... [Same as before] ...
    pass

def categorize_service(subject, labels):
    # ... [Same as before] ...
    pass

def load_processed_ids():
    if os.path.exists('processed_ids.pickle'):
        with open('processed_ids.pickle', 'rb') as f:
            return pickle.load(f)
    else:
        return set()

def save_processed_ids(processed_ids):
    with open('processed_ids.pickle', 'wb') as f:
        pickle.dump(processed_ids, f)

def main():
    service = get_gmail_service()
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
