from __future__ import annotations
import imaplib
import email
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from email.header import decode_header

# IMAP Configuration for Gmail (FREE - No API credits needed)
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

# Email keywords that indicate invoice/PO emails
INVOICE_KEYWORDS = ["invoice", "billing", "payment due", "amount due", "statement", "invoice number", "inv-", "inv #"]
PO_KEYWORDS = ["purchase order", "po number", "purchase order number", "order confirmation", "po-", "po #", "po_"]
# Attachment filename patterns
INVOICE_FILE_PATTERNS = ["invoice", "inv", "bill", "statement"]
PO_FILE_PATTERNS = ["po", "purchase", "order"]


class IMAPEmailIntegration:
	"""Free IMAP-based email integration - no API credits required"""
	
	def __init__(self, email_address: str = "examplecode14@gmail.com", app_password: Optional[str] = None) -> None:
		self.email_address = email_address
		self.app_password = app_password
		self.mail: Optional[imaplib.IMAP4_SSL] = None

	def authenticate(self, password: str) -> bool:
		"""Authenticate with Gmail IMAP using email and app password"""
		try:
			self.mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
			self.mail.login(self.email_address, password)
			self.app_password = password
			return True
		except Exception as e:
			return False

	def _decode_mime_words(self, s: str) -> str:
		"""Decode MIME encoded email headers"""
		if not s:
			return ""
		decoded_fragments = decode_header(s)
		return "".join([fragment[0].decode(fragment[1] or 'utf-8', errors='ignore') if isinstance(fragment[0], bytes) else str(fragment[0]) for fragment in decoded_fragments])

	def _is_invoice_email(self, subject: str, body: str, attachments: List[tuple]) -> bool:
		"""Classify if email contains invoice - checks subject/body AND attachment names"""
		text = (subject + " " + body).lower()
		# Check keywords in email text
		if any(kw in text for kw in INVOICE_KEYWORDS):
			return True
		# Check attachment filenames
		for filename, _ in attachments:
			if any(pattern in filename.lower() for pattern in INVOICE_FILE_PATTERNS):
				return True
		return False

	def _is_po_email(self, subject: str, body: str, attachments: List[tuple]) -> bool:
		"""Classify if email contains purchase order - checks subject/body AND attachment names"""
		text = (subject + " " + body).lower()
		# Check keywords in email text
		if any(kw in text for kw in PO_KEYWORDS):
			return True
		# Check attachment filenames
		for filename, _ in attachments:
			if any(pattern in filename.lower() for pattern in PO_FILE_PATTERNS):
				return True
		return False

	def _get_attachments(self, msg: email.message.Message) -> List[tuple[str, bytes]]:
		"""Extract attachments from email message"""
		attachments = []
		for part in msg.walk():
			if part.get_content_disposition() == 'attachment':
				filename = part.get_filename()
				if filename:
					filename = self._decode_mime_words(filename)
					if any(filename.lower().endswith(ext) for ext in ['.pdf', '.png', '.jpg', '.jpeg']):
						payload = part.get_payload(decode=True)
						if payload:
							attachments.append((filename, payload))
		return attachments

	def fetch_unread_invoices(self, max_results: int = 10) -> List[Dict[str, Any]]:
		"""Fetch unread emails with invoice attachments using IMAP"""
		if not self.mail:
			return []
		try:
			self.mail.select("inbox")
			status, messages = self.mail.search(None, 'UNSEEN')
			if status != 'OK':
				return []
			
			email_ids = messages[0].split()
			invoices = []
			for email_id in reversed(email_ids[-max_results*3:]):  # Check more emails to find matches
				try:
					status, msg_data = self.mail.fetch(email_id, '(RFC822)')
					if status != 'OK':
						continue
					
					msg = email.message_from_bytes(msg_data[0][1])
					subject = self._decode_mime_words(msg['Subject'] or '')
					
					# Get body
					body = ""
					if msg.is_multipart():
						for part in msg.walk():
							content_type = part.get_content_type()
							if content_type == 'text/plain' or content_type == 'text/html':
								try:
									body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
								except:
									pass
					else:
						try:
							body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
						except:
							pass
					
					# Get attachments first to check filenames
					attachments = self._get_attachments(msg)
					if attachments:
						# Check if email is invoice based on content AND attachments
						# This now checks attachment filenames too (e.g., "Invoice2.png")
						is_invoice = self._is_invoice_email(subject, body, attachments)
						if is_invoice:
							# Include ALL PDF/image attachments from matching emails
							for filename, data in attachments:
								invoices.append({
									'email_id': email_id.decode(),
									'subject': subject or '(no subject)',
									'filename': filename,
									'data': data,
									'date': datetime.now().isoformat(),
									'type': 'invoice'
								})
								if len(invoices) >= max_results:
									break
				except Exception as e:
					continue
			return invoices[:max_results]
		except Exception:
			return []

	def fetch_unread_pos(self, max_results: int = 10) -> List[Dict[str, Any]]:
		"""Fetch unread emails with PO attachments using IMAP"""
		if not self.mail:
			return []
		try:
			self.mail.select("inbox")
			status, messages = self.mail.search(None, 'UNSEEN')
			if status != 'OK':
				return []
			
			email_ids = messages[0].split()
			pos = []
			for email_id in reversed(email_ids[-max_results*3:]):
				try:
					status, msg_data = self.mail.fetch(email_id, '(RFC822)')
					if status != 'OK':
						continue
					
					msg = email.message_from_bytes(msg_data[0][1])
					subject = self._decode_mime_words(msg['Subject'] or '')
					
					# Get body
					body = ""
					if msg.is_multipart():
						for part in msg.walk():
							content_type = part.get_content_type()
							if content_type == 'text/plain' or content_type == 'text/html':
								try:
									body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
								except:
									pass
					else:
						try:
							body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
						except:
							pass
					
					# Get attachments first to check filenames
					attachments = self._get_attachments(msg)
					if attachments:
						# Check if email is PO based on content AND attachments
						# This now checks attachment filenames too (e.g., "PO2.png")
						is_po = self._is_po_email(subject, body, attachments)
						if is_po:
							# Include ALL PDF/image attachments from matching emails
							for filename, data in attachments:
								pos.append({
									'email_id': email_id.decode(),
									'subject': subject or '(no subject)',
									'filename': filename,
									'data': data,
									'date': datetime.now().isoformat(),
									'type': 'po'
								})
								if len(pos) >= max_results:
									break
				except Exception as e:
					continue
			return pos[:max_results]
		except Exception:
			return []

	def mark_as_read(self, message_id: str) -> bool:
		"""Mark email as read"""
		if not self.mail:
			return False
		try:
			self.mail.store(message_id.encode(), '+FLAGS', '\\Seen')
			return True
		except Exception:
			return False

	def close(self) -> None:
		"""Close IMAP connection"""
		if self.mail:
			try:
				self.mail.close()
				self.mail.logout()
			except:
				pass


def update_master_csv(results: List[Dict[str, Any]], csv_path: str = "master_invoice_po_records.csv") -> None:
	"""Append verified results to master CSV file"""
	if not results:
		return
	df_new = pd.DataFrame(results)
	if os.path.exists(csv_path):
		df_existing = pd.read_csv(csv_path)
		df_combined = pd.concat([df_existing, df_new], ignore_index=True)
	else:
		df_combined = df_new
	df_combined.to_csv(csv_path, index=False)

