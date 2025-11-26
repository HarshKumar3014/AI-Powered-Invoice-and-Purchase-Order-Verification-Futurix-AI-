# 🤖 AI-Powered Invoice and Purchase Order Verification System

**Futurix AI · Enterprise-Ready Verification System**

An intelligent Streamlit-based application that automatically extracts, verifies, and reconciles key information from invoices and purchase orders using OCR and AI-powered field extraction.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

### 📄 Document Processing
- **Multi-format Support**: PDF and image files (PNG, JPG, JPEG)
- **Smart OCR**: Automatic fallback system (PaddleOCR → EasyOCR → Tesseract)
- **Native PDF Extraction**: Uses PyPDF2 for digital PDFs, OCR for scanned documents
- **Real-time Preview**: View document previews before processing

### 🔍 Intelligent Data Extraction
- **Key Field Extraction**: Vendor, date, total amount, currency, PO/Invoice numbers
- **Regex-based Parsing**: Fast, accurate field extraction with pattern matching
- **OpenAI Integration** (Optional): Enhanced extraction using GPT-4o/GPT-4o-mini
- **Flexible Matching**: Dynamic field detection based on available data

### ✅ Verification & Comparison
- **Automatic Matching**: Compares invoice vs. purchase order fields
- **Discrepancy Detection**: Highlights mismatches in vendor, amounts, dates, and order numbers
- **Smart Normalization**: 
  - Company name matching (handles "Pvt. Ltd.", "Inc.", etc.)
  - Numeric ID core matching (e.g., INV-20251030 vs PO-20251030)
  - Date format normalization
  - Amount tolerance matching
- **Color-coded Results**: Visual status indicators (green=match, red=mismatch, amber=missing)

### 📊 Export & Reporting
- **CSV Export**: Download comparison results
- **Master CSV**: Automatic compilation of all processed records
- **Structured Output**: Clean, formatted data for ERP/accounting integration

### 📧 Email Automation (Bonus Feature)
- **Gmail Integration**: FREE IMAP-based email processing (no API credits needed)
- **Automatic Detection**: Identifies invoice/PO emails by subject, body, or attachment filenames
- **Real-time Processing**: Fetches unread emails, processes attachments, updates CSV
- **Smart Classification**: Recognizes invoices and purchase orders from attachment names

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- For OCR: One of the following:
  - EasyOCR (recommended): `pip install easyocr`
  - Tesseract: `pip install pytesseract` + system installation
  - PaddleOCR (Linux/Windows only)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/HarshKumar3014/AI-Powered-Invoice-and-Purchase-Order-Verification-Futurix-AI-.git
   cd AI-Powered-Invoice-and-Purchase-Order-Verification-Futurix-AI-
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install OCR backend** (choose one)
   ```bash
   # EasyOCR (Recommended)
   pip install easyocr
   
   # OR Tesseract (macOS)
   brew install tesseract poppler
   pip install pytesseract
   ```

4. **Run the application**
   ```bash
   streamlit run main_app.py
   ```

5. **Open in browser**
   - The app will automatically open at `http://localhost:8501`

## 📖 Usage Guide

### Manual Upload & Verification

1. **Upload Documents**
   - Click "📤 Manual Upload" tab
   - Upload an Invoice (PDF/Image)
   - Upload a Purchase Order (PDF/Image)
   - View document previews

2. **Process & Verify**
   - Click "🚀 Process & Verify"
   - Review extracted fields from both documents
   - Check the comparison table for matches/mismatches
   - Download results as CSV

3. **Settings** (Sidebar)
   - Enable "Use OpenAI for field extraction" for enhanced accuracy
   - Select model (gpt-4o-mini or gpt-4o)
   - Requires `OPENAI_API_KEY` environment variable

### Email Automation (Optional)

1. **Setup Gmail App Password**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable 2-Step Verification
   - Generate App Password: Security → App passwords → Mail → Other → "Futurix AI"
   - Copy the 16-character password

2. **Configure in App**
   - Go to "📧 Email Automation" tab
   - Enter Gmail address
   - Paste App Password
   - Click "🔐 Connect to Gmail"

3. **Process Emails**
   - Set max emails to process
   - Enable "Auto-update master CSV" if desired
   - Click "🔄 Fetch & Process Emails"
   - Review processed documents
   - Download master CSV

📖 **Detailed setup**: See [IMAP_SETUP.md](IMAP_SETUP.md)

## 📁 Project Structure

```
OCR/
├── main_app.py                 # Streamlit entry point
├── ui_components.py            # UI components and styling
├── ocr_utils.py               # OCR backend with fallback system
├── compare_utils.py            # Field comparison and normalization
├── email_utils_imap.py        # Gmail IMAP integration (FREE)
├── email_utils.py             # Gmail API integration (legacy, optional)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── IMAP_SETUP.md              # Email automation setup guide
└── GMAIL_SETUP.md             # Gmail API setup (if using API method)
```

## 🔧 Configuration

### Environment Variables

```bash
# Optional: For OpenAI-enhanced extraction
export OPENAI_API_KEY="sk-your-api-key-here"
```

### OCR Backend Selection

The app automatically selects the best available OCR backend:
1. **PaddleOCR** (Linux/Windows, highest accuracy)
2. **EasyOCR** (Cross-platform, good accuracy)
3. **Tesseract** (Cross-platform, fast, lighter)

Install at least one for the app to function.

## 📊 Output Format

### Extracted Fields
- `vendor`: Company/vendor name
- `date`: Transaction date
- `total`: Total amount
- `currency`: Currency code (USD, EUR, etc.)
- `po_number`: Purchase Order or Invoice number

### Comparison Status
- **match**: Values match between invoice and PO
- **mismatch**: Values differ
- **missing**: Field not found in one or both documents

## 🛠️ Technology Stack

- **Framework**: Streamlit
- **OCR**: PaddleOCR / EasyOCR / Tesseract
- **PDF Processing**: PyPDF2, pdf2image
- **Data Processing**: Pandas, NumPy
- **AI Enhancement**: OpenAI API (optional)
- **Email**: IMAP (built-in, free)

## 🔒 Security Notes

- Gmail App Passwords are safer than regular passwords
- Never commit `credentials.json`, `token.json`, or `.env` files
- App passwords can be revoked anytime from Google Account settings
- All email processing happens locally

## 🐛 Troubleshooting

### OCR Not Working
- Ensure at least one OCR backend is installed
- For Tesseract: Check system installation (`brew install tesseract` on macOS)
- For EasyOCR: First run downloads models (~500MB)

### PDF Preview Not Showing
- Install poppler: `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux)

### Email Connection Failed
- Verify 2-step verification is enabled
- Use 16-character App Password (not regular password)
- Check internet connection
- Ensure IMAP is enabled in Gmail settings

### Empty Extraction Results
- Check if PDF has selectable text (try native extraction first)
- Verify document quality for OCR
- Enable OpenAI extraction for better accuracy

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 👤 Author

**Harsh Kumar**

- GitHub: [@HarshKumar3014](https://github.com/HarshKumar3014)
- Email: kumarharsh3014@gmail.com
- GitHub: [@pranaysensei31](https://github.com/pranaysensei31)
- Email: pranaymahajan3106@gmail.com


## 🙏 Acknowledgments

- Streamlit for the excellent framework
- OCR libraries: PaddleOCR, EasyOCR, Tesseract
- Google for Gmail IMAP access

## 📄 Related Documentation

- [IMAP Email Setup Guide](IMAP_SETUP.md)
- [Gmail API Setup (Alternative)](GMAIL_SETUP.md)

---

