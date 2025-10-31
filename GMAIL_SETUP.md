# Gmail API Setup Guide

## Prerequisites
- Google Account (examplecode14@gmail.com)
- Google Cloud Console access

## Step-by-Step Setup

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it "Futurix AI Email" (or your preferred name)
4. Click "Create"

### 2. Enable Gmail API
1. In the project dashboard, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click "Enable"

### 3. Create OAuth 2.0 Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: External (or Internal if using Google Workspace)
   - App name: "Futurix AI Invoice Processor"
   - User support email: your email
   - Developer contact: your email
   - Click "Save and Continue"
   - Scopes: Add `https://www.googleapis.com/auth/gmail.readonly` and `https://www.googleapis.com/auth/gmail.modify`
   - Click "Save and Continue" → "Save and Continue" → "Back to Dashboard"
4. Application type: **Desktop app**
5. Name: "Futurix AI Desktop Client"
6. Click "Create"
7. Click "Download JSON"
8. Rename downloaded file to `credentials.json`
9. Place `credentials.json` in the project root directory (`/Volumes/Development/OCR/`)

### 4. First-Time Authentication
1. Run the Streamlit app: `python3 -m streamlit run main_app.py`
2. Navigate to "📧 Email Automation" tab
3. Click "🔐 Authenticate with Gmail"
4. Browser will open - sign in with **examplecode14@gmail.com**
5. Allow permissions for Gmail access
6. Token will be saved as `token.json` automatically

### 5. Email Configuration
The system is configured for: **examplecode14@gmail.com**

It will:
- ✅ Detect emails with invoice/PO keywords
- ✅ Extract PDF/image attachments
- ✅ Process using OCR
- ✅ Auto-update master CSV file
- ✅ Mark emails as read after processing

## Troubleshooting

**"credentials.json not found"**
- Ensure file is in project root with exact name `credentials.json`

**"Authentication failed"**
- Check internet connection
- Verify Gmail API is enabled in Cloud Console
- Ensure OAuth consent screen is configured

**"No emails found"**
- Check that emails are unread
- Verify emails have PDF/image attachments
- Ensure email subject/body contains invoice/PO keywords

## Security Notes
- `credentials.json` contains sensitive OAuth client info - don't commit to git
- `token.json` contains access tokens - keep secure
- Add both files to `.gitignore`

