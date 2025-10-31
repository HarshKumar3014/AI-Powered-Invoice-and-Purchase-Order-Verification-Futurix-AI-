# IMAP Email Setup Guide (FREE - No Credits Required)

## ✅ Why IMAP?
- **Completely FREE** - No Google Cloud credits needed
- **No API setup** - Uses standard email protocols
- **Simple authentication** - Just need a Gmail App Password
- **Same functionality** - Fetches emails, attachments, processes invoices/POs

## Quick Setup (3 Steps)

### Step 1: Enable 2-Step Verification
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click **2-Step Verification**
3. Follow prompts to enable (if not already enabled)

### Step 2: Generate App Password
1. Still in Security settings, scroll to **App passwords**
2. Click **App passwords**
3. Select:
   - App: **Mail**
   - Device: **Other (Custom name)**
   - Name: `Futurix AI Invoice Processor`
4. Click **Generate**
5. **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)

### Step 3: Use in App
1. Open the **Email Automation** tab
2. Enter your Gmail: `examplecode14@gmail.com`
3. Paste the 16-character app password
4. Click **Connect to Gmail**
5. Done! ✅

## Security Notes
- ✅ App passwords are safer than your main password
- ✅ You can revoke app passwords anytime
- ✅ Each app password works for one app only
- ⚠️ Never commit app passwords to git

## Troubleshooting

**"Connection failed"**
- Verify 2-step verification is enabled
- Check that you're using the 16-character app password (not regular password)
- Remove spaces from the app password if copying/pasting

**"No emails found"**
- Check that emails are unread
- Verify emails have PDF/image attachments
- Ensure subject/body contains invoice/PO keywords

**"IMAP not enabled"**
- IMAP is enabled by default on Gmail
- If issues persist, check Gmail Settings → Forwarding and POP/IMAP → Enable IMAP

## Features
- ✅ Fetches unread emails with attachments
- ✅ Detects invoices and purchase orders
- ✅ Extracts PDF/image attachments
- ✅ Processes with OCR automatically
- ✅ Updates master CSV in real-time
- ✅ Marks emails as read after processing

