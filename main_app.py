from __future__ import annotations
import streamlit as st
import pandas as pd
import os
from ui_components import render_header, upload_pair, show_extraction, show_comparison, csv_download_button
from ocr_utils import OCRBackend, extract_fields
from compare_utils import compare_records
from email_utils_imap import IMAPEmailIntegration, update_master_csv

# Streamlit App

def _detect_filetype(upload_bytes: bytes) -> str:
	return "pdf" if upload_bytes[:4] == b"%PDF" else "image"


def _process_email_automation(use_openai: bool, model: str) -> None:
	"""Handle Gmail email automation feature using IMAP (FREE - no credits needed)"""
	st.header("📧 Email Automation")
	st.caption("✅ **FREE** - Uses IMAP (no API credits required)")
	
	# Setup instructions
	with st.expander("📖 Quick Setup Guide (FREE)"):
		st.markdown("""
		### Step 1: Create Gmail App Password
		1. Go to your Google Account: https://myaccount.google.com/
		2. Click **Security** → **2-Step Verification** (enable if not already)
		3. Scroll down to **App passwords**
		4. Select **Mail** and **Other (Custom name)**
		5. Name it "Futurix AI Invoice Processor"
		6. Click **Generate**
		7. Copy the 16-character password (you'll use this below)
		
		### Step 2: Enter Credentials
		- Email: **examplecode14@gmail.com**
		- Password: Your 16-character app password (NOT your regular Gmail password)
		
		**✅ That's it! No API setup, no credits, completely free.**
		""")
	
	# Email authentication
	email_address = st.text_input("📧 Gmail Address", value="examplecode14@gmail.com", help="Your Gmail address")
	
	if not st.session_state.get("imap_authenticated", False):
		app_password = st.text_input(
			"🔐 Gmail App Password", 
			type="password",
			help="16-character app password from Google Account settings (NOT your regular password)"
		)
		if st.button("🔐 Connect to Gmail"):
			if app_password:
				with st.spinner("Connecting to Gmail via IMAP..."):
					imap = IMAPEmailIntegration(email_address=email_address)
					if imap.authenticate(app_password):
						st.session_state["imap_authenticated"] = True
						st.session_state["imap"] = imap
						st.session_state["email_address"] = email_address
						st.success("✅ Connected successfully!")
						st.rerun()
					else:
						st.error("❌ Connection failed. Check your email and app password.")
			else:
				st.warning("⚠️ Please enter your Gmail app password.")
		return
	
	imap = st.session_state.get("imap")
	if not imap:
		st.error("Session expired. Please reconnect.")
		st.session_state["imap_authenticated"] = False
		if st.button("🔄 Reconnect"):
			st.session_state["imap_authenticated"] = False
			st.rerun()
		return
	
	st.success(f"✅ Connected to {st.session_state.get('email_address', email_address)}")
	
	col1, col2 = st.columns(2)
	with col1:
		max_emails = st.number_input("Max emails to process", min_value=1, max_value=50, value=10)
	with col2:
		auto_csv = st.checkbox("Auto-update master CSV", value=True)
	
	if st.button("🔄 Fetch & Process Emails"):
		with st.spinner("Fetching and processing emails..."):
			ocr = OCRBackend()
			if ocr.kind == "none":
				st.error("OCR backend required for email processing")
				return
			
			# Show debug info
			with st.expander("🔍 Debug Info", expanded=False):
				try:
					imap.mail.select("inbox")
					status, messages = imap.mail.search(None, 'UNSEEN')
					if status == 'OK':
						email_ids = messages[0].split()
						st.info(f"Found {len(email_ids)} unread emails")
					else:
						st.warning("Could not search inbox")
				except Exception as e:
					st.error(f"Debug error: {str(e)}")
			
			invoices = imap.fetch_unread_invoices(max_results=max_emails)
			pos = imap.fetch_unread_pos(max_results=max_emails)
			
			# Show what was found
			if invoices or pos:
				st.info(f"Found {len(invoices)} invoice(s) and {len(pos)} PO(s) with matching attachments")
			
			processed = []
			for inv_item in invoices:
				with st.expander(f"📄 Processing: {inv_item['filename']}", expanded=False):
					text = ocr.image_bytes_to_text(inv_item['data'], _detect_filetype(inv_item['data']))
					data = extract_fields(text, use_openai=use_openai, model=model) if text else {}
					if text:
						data["_raw"] = text
					data['email_id'] = inv_item['email_id']
					data['email_subject'] = inv_item['subject']
					data['source'] = 'email'
					data['processed_date'] = inv_item['date']
					processed.append(data)
					show_extraction(data, f"Invoice: {inv_item['filename']}")
					imap.mark_as_read(inv_item['email_id'])
			
			for po_item in pos:
				with st.expander(f"📋 Processing: {po_item['filename']}", expanded=False):
					text = ocr.image_bytes_to_text(po_item['data'], _detect_filetype(po_item['data']))
					data = extract_fields(text, use_openai=use_openai, model=model) if text else {}
					if text:
						data["_raw"] = text
					data['email_id'] = po_item['email_id']
					data['email_subject'] = po_item['subject']
					data['source'] = 'email'
					data['processed_date'] = po_item['date']
					processed.append(data)
					show_extraction(data, f"PO: {po_item['filename']}")
					imap.mark_as_read(po_item['email_id'])
			
			if processed and auto_csv:
				update_master_csv(processed)
				st.success(f"✅ Processed {len(processed)} documents and updated master CSV!")
			elif processed:
				st.success(f"✅ Processed {len(processed)} documents!")
			
			if not processed:
				st.info("ℹ️ No new invoice/PO emails found.")


def main() -> None:
	render_header()
	with st.sidebar:
		st.header("⚙️ Settings")
		st.markdown("---")
		use_openai = st.checkbox("Use OpenAI for field extraction", value=False, help="Enable AI-powered extraction refinement (requires OPENAI_API_KEY)")
		model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0, disabled=not use_openai)
		st.caption("💡 Set OPENAI_API_KEY environment variable to enable AI extraction")
		st.markdown("---")
		st.caption("**Futurix AI** · Invoice/PO Verification System")
	
	# Tab navigation
	tab1, tab2 = st.tabs(["📤 Manual Upload", "📧 Email Automation"])
	
	with tab1:
		inv_bytes, po_bytes = upload_pair()
		st.markdown("---")
		col_btn, _ = st.columns([1, 5])
		with col_btn:
			process = st.button("🚀 Process & Verify", type="primary", use_container_width=True)
		if not process:
			st.info("ℹ️ Upload an Invoice and a Purchase Order, then click 'Process & Verify' to begin.")
		else:
			with st.spinner("🔄 Processing documents with OCR..."):
				ocr = OCRBackend()
				if ocr.kind == "none":
					st.error("❌ **No OCR backend available**\n\nPlease install one of:\n- `pip install easyocr` (recommended)\n- `pip install pytesseract` + system tesseract\n- PaddleOCR (Linux/Windows only)")
				else:
					inv_text = po_text = ""
					if inv_bytes:
						try:
							inv_text = ocr.image_bytes_to_text(inv_bytes, _detect_filetype(inv_bytes))
						except Exception as e:
							st.error(f"Failed to process invoice: {str(e)}")
							inv_text = ""
					if po_bytes:
						try:
							po_text = ocr.image_bytes_to_text(po_bytes, _detect_filetype(po_bytes))
						except Exception as e:
							st.error(f"Failed to process PO: {str(e)}")
							po_text = ""
					
					if not inv_text and inv_bytes:
						st.warning("⚠️ Invoice text extraction returned empty. The document might be scanned or unreadable.")
					if not po_text and po_bytes:
						st.warning("⚠️ PO text extraction returned empty. The document might be scanned or unreadable.")
					
					if inv_text or po_text:
						st.success("✅ Document processing complete!")
						st.markdown("---")
						
						inv_data = extract_fields(inv_text, use_openai=use_openai, model=model) if inv_text else {}
						po_data = extract_fields(po_text, use_openai=use_openai, model=model) if po_text else {}
						# attach raw OCR preview for debugging
						if inv_text:
							inv_data["_raw"] = inv_text
						if po_text:
							po_data["_raw"] = po_text

						show_extraction(inv_data, "Invoice Extraction")
						show_extraction(po_data, "PO Extraction")

						df, mismatches = compare_records(inv_data, po_data)
						show_comparison(df)

						csv_download_button(df)
						if mismatches:
							st.warning(f"Detected {mismatches} mismatched fields.")
						else:
							st.success("All fields match.")
					else:
						st.error("❌ Could not extract text from either document. Please check file formats and try again.")
	
	with tab2:
		_process_email_automation(use_openai, model)
		
		# Show master CSV if exists
		if os.path.exists("master_invoice_po_records.csv"):
			st.markdown("---")
			st.subheader("📊 Master Records")
			df_master = pd.read_csv("master_invoice_po_records.csv")
			st.dataframe(df_master, use_container_width=True)
			st.download_button(
				"📥 Download Master CSV",
				data=df_master.to_csv(index=False),
				file_name="master_invoice_po_records.csv",
				mime="text/csv"
			)
		
		# Cleanup connection on tab close
		if st.session_state.get("imap"):
			try:
				# Connection stays open for session - will close on app restart
				pass
			except:
				pass


if __name__ == "__main__":
	main()
