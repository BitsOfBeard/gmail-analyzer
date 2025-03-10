# Gmail Analyzer Script

This Python script connects to your Gmail account using the Gmail API to analyze and categorize your emails. It processes emails in batches, allowing you to scan your entire mailbox over multiple runs. Results are stored in a CSV file for external analysis.

## Features

- **Batch Processing**: Processes emails in user-defined batches (default: 1000/run)
- **Email Categorization**: Categorizes emails using Gmail labels and content analysis
- **Persistent Tracking**: Maintains processing state between runs
- **CSV Export**: Generates `email_analysis.csv` with sender statistics
- **Safe Authentication**: OAuth 2.0 with separate credential storage

## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Configuration](#configuration)
- [Usage](#usage)
- [Viewing Results](#viewing-results)
- [Important Notes](#important-notes)
- [License](#license)

## Prerequisites

- Python 3.6+
- Google account with Gmail enabled
- Internet connection

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/BitsOfBeard/gmail-analyzer.git
cd gmail-analyzer
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv  # macOS/Linux
python -m venv venv   # Windows
```

### 3. Activate Environment
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate    # Windows
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Google API
1. Create project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Gmail API
3. Create OAuth 2.0 Desktop credentials
4. Download as `credentials.json` to project root

### 6. First Run
```bash
python gmail_analyzer.py
# Follow browser authentication prompts
```

## Configuration

Edit these constants in the script:
```python
BATCH_SIZE = 1000  # Emails per run
CSV_FILENAME = 'email_analysis.csv'  # Output file
```

## Usage

```bash
# Process next batch
python gmail_analyzer.py --batch-size 500

# Check progress
python gmail_analyzer.py --export-only
```

## Viewing Results

The CSV file contains:
- Service/company name
- Email address
- Communication type
- Email count
- First/last seen timestamps

**Analysis methods**:
```bash
# Terminal preview
column -s, -t < email_analysis.csv | less -#2 -N -S

# Spreadsheet
open email_analysis.csv  # macOS
start email_analysis.csv  # Windows

# Python/Pandas
import pandas as pd
df = pd.read_csv('email_analysis.csv')
print(df.sort_values('count', ascending=False).head(10))
```

## Important Notes

### File Management
| File                   | Purpose                                | Security  |
|------------------------|----------------------------------------|-----------|
| `credentials.json`    | Google API credentials                 | 🔒 Secret |
| `gmail_token.pickle`  | Encrypted session tokens               | 🔒 Secret |
| `processed_ids.pickle`| Tracked email IDs                      | 🔐 Private|
| `email_analysis.csv`   | Aggregated sender stats                | 🔐 Private|

### Maintenance
```bash
# Reset processing
rm processed_ids.pickle

# Full reset
rm gmail_token.pickle processed_ids.pickle email_analysis.csv
```

### Security
- Never commit `*.pickle` or `credentials.json`
- Revoke access at [Google Security Settings](https://myaccount.google.com/permissions)

## License
MIT License - See [LICENSE](LICENSE)
