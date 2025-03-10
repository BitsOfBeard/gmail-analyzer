# Gmail Analyzer Script

This Python script connects to your Gmail account using the Gmail API to analyze and categorize your emails. It processes emails in batches, allowing you to scan your entire mailbox over multiple runs. The script outputs a table summarizing the services or companies that have sent you emails, along with the type of communication and the number of emails received.

## Features

- **Batch Processing**: Processes emails in user-defined batches to manage execution time and resources.
- **Email Categorization**: Categorizes emails into Personal, Social, Promotions, Updates, Forums, Subscription, or Data Holder.
- **Sender Analysis**: Extracts sender information and counts the number of emails from each sender.
- **Progress Persistence**: Remembers processed emails between runs to avoid duplication.
- **Customizable**: Easily adjust batch sizes and categories as needed.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  1. [Clone the Repository](#1-clone-the-repository)
  2. [Create a Virtual Environment](#2-create-a-virtual-environment)
  3. [Activate the Virtual Environment](#3-activate-the-virtual-environment)
  4. [Install Dependencies](#4-install-dependencies)
  5. [Obtain Google API Credentials](#5-obtain-google-api-credentials)
  6. [Run the Script](#6-run-the-script)
- [Configuration](#configuration)
- [Usage](#usage)
- [Important Notes](#important-notes)
- [License](#license)

## Prerequisites

- Python 3.6 or higher
- A Google account with Gmail enabled
- Internet connection

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/BitsOfBeard/gmail-analyzer.git
cd gmail-analyzer
```

### 2. Create a Virtual Environment

Create a virtual environment to manage dependencies.

On macOS/Linux:

```bash
python3 -m venv venv
```

On Windows:

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

On macOS/Linux:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

Install the required Python packages using pip.

```bash
pip install -r requirements.txt
```

Contents of `requirements.txt`:

```
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
prettytable
```

### 5. Obtain Google API Credentials

#### a. Set Up a Project in Google Cloud Console

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the Gmail API for your project:
   - Navigate to **APIs & Services > Library**.
   - Search for **Gmail API** and click **Enable**.

#### b. Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**.
2. Click **Create Credentials** and select **OAuth client ID**.
3. Choose **Desktop app** as the application type.
4. Name your client (e.g., "Gmail Analyzer") and click **Create**.
5. Click **Download JSON** to get your `credentials.json` file.
6. Place the `credentials.json` file in the root directory of the cloned repository.

> **Important**: Do not share your `credentials.json` file or upload it to any public repository.

### 6. Run the Script

With everything set up, you can run the script:

```bash
python gmail_analyzer.py
```

On the first run, a browser window will open for you to authorize the application.
After authorization, the script will begin processing your emails in batches.

## Configuration

You can adjust the batch size by modifying the `BATCH_SIZE` variable in the script:

```python
BATCH_SIZE = 1000  # Number of emails to process per run
```

## Usage

- **Incremental Processing**: Run the script multiple times to process all emails. It will pick up where it left off.
- **Viewing Results**: After each run, the script outputs a table of the services and a summary of categories.
- **Resetting Progress**: To start over, delete the `processed_ids.pickle` file.

## Important Notes

### Sensitive Information

- `credentials.json`: Contains your OAuth 2.0 Client ID and Client Secret. Do not commit this file to any public repository.
- `token.pickle`: Stores your access and refresh tokens after authorization. This file should also be kept private.

### .gitignore File

Ensure that sensitive files are excluded from version control by adding them to your `.gitignore` file:

```
credentials.json
token.pickle
processed_ids.pickle
```

### API Quotas and Limits

Be mindful of Gmail API usage limits to avoid exceeding quotas.
For more information, refer to the [Gmail API Usage Limits](https://developers.google.com/gmail/api/reference/quota).

### Privacy Considerations

The script processes your personal emails. Ensure that any output data is handled securely.
Review and comply with Google's [API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
