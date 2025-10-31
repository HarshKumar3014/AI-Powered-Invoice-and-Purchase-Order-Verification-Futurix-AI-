from __future__ import annotations
import os
import base64
import io
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']
GMAIL_USER = "examplecode14@gmail.com"

# Email keywords that indicate invoice/PO emails
INVOICE_KEYWORDS = ["invoice", "billing", "payment due", "amount due", "statement"]
PO_KEYWORDS = ["purchase order", "po number", "purchase order number", "order confirmation"]


class GmailIntegration:
	def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json") -> None:
		self.credentials_path = credentials_path
		self.token_path = token_path
		self.service = None
		self.creds: Optional[Credentials] = None

	def authenticate(self) -> bool:
		"""Authenticate with Gmail API using OAuth2"""
		if os.path.exists(self.token_path):
			self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
		if not self.creds or not self.creds.valid:
			if self.creds and self.creds.expired and self.creds.refresh_token:
				self.creds.refresh(Request())
			else:
				if not os.path.exists(self.credentials_path):
					return False
				flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
				self.creds = flow.run_local_server(port=0)
			with open(self.token_path, 'w') as token:
				token.write(self.creds.to_json())
		try:
			self.service = build('gmail', 'v1', credentials=self.creds)
			return True
		except HttpError as e:
			return False

	def _is_invoice_email(self, subject: str, body: str) -> bool:
		"""Classify if email contains invoice"""
		text = (subject + " " + body).lower()
		return any(kw in text for kw in INVOICE_KEYWORDS)

	def _is_po_email(self, subject: str, body: str) -> bool:
		"""Classify if email contains purchase order"""
		text = (subject + " " + body).lower()
		return any(kw in text for kw in PO_KEYWORDS)

	def _get_attachments(self, message_id: str) -> List[Tuple[str, bytes]]:
		"""Extract attachments from email message"""
		attachments = []
		try:
			message = self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
			for part in message.get('payload', {}).get('parts', []):
				if part.get('filename') and part.get('body', {}).get('attachmentId'):
					att_id = part['body']['attachmentId']
					att = self.service.users().messages().attachments().get(
						userId='me', messageId=message_id, id=att_id
					).execute()
					file_data = base64.urlsafe_b64decode(att['data'])
					filename = part['filename']
					if any(filename.lower().endswith(ext) for ext in ['.pdf', '.png', '.jpg', '.jpeg']):
						attachments.append((filename, file_data))
		except HttpError:
			pass
		return attachments

	def fetch_unread_invoices(self, max_results: int = 10) -> List[Dict[str, Any]]:
		"""Fetch unread emails with invoice attachments"""
		if not self.service:
			return []
		try:
			# Search for unread emails with invoice keywords or from any sender
			query = 'is:unread has:attachment'
			results = self.service.users().messages().list(userId='me', q=query, maxResults=max_results*2).execute()
			messages = results.get('messages', [])
			invoices = []
			for msg in messages[:max_results]:
				msg_obj = self.service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
				headers = msg_obj.get('payload', {}).get('headers', [])
				subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
				body_snippet = msg_obj.get('snippet', '')
				if self._is_invoice_email(subject, body_snippet):
					attachments = self._get_attachments(msg['id'])
					if attachments:
						for filename, data in attachments:
							invoices.append({
								'email_id': msg['id'],
								'subject': subject,
								'filename': filename,
								'data': data,
								'date': datetime.now().isoformat(),
								'type': 'invoice'
							})
						if len(invoices) >= max_results:
							break
			return invoices[:max_results]
		except HttpError:
			return []

	def fetch_unread_pos(self, max_results: int = 10) -> List[Dict[str, Any]]:
		"""Fetch unread emails with PO attachments"""
		if not self.service:
			return []
		try:
			# Search for unread emails with attachments
			query = 'is:unread has:attachment'
			results = self.service.users().messages().list(userId='me', q=query, maxResults=max_results*2).execute()
			messages = results.get('messages', [])
			pos = []
			for msg in messages[:max_results]:
				msg_obj = self.service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
				headers = msg_obj.get('payload', {}).get('headers', [])
				subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
				body_snippet = msg_obj.get('snippet', '')
				if self._is_po_email(subject, body_snippet):
					attachments = self._get_attachments(msg['id'])
					if attachments:
						for filename, data in attachments:
							pos.append({
								'email_id': msg['id'],
								'subject': subject,
								'filename': filename,
								'data': data,
								'date': datetime.now().isoformat(),
								'type': 'po'
							})
						if len(pos) >= max_results:
							break
			return pos[:max_results]
		except HttpError:
			return []

	def mark_as_read(self, message_id: str) -> bool:
		"""Mark email as read"""
		if not self.service:
			return False
		try:
			self.service.users().messages().modify(
				userId='me',
				id=message_id,
				body={'removeLabelIds': ['UNREAD']}
			).execute()
			return True
		except HttpError:
			return False


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

