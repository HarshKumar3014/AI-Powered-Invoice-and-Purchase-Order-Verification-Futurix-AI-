from __future__ import annotations
from typing import Optional, List
import io
import re
from PIL import Image, ImageOps, ImageFilter

# Try PaddleOCR first, fallback to EasyOCR, then Tesseract
class OCRBackend:
	def __init__(self) -> None:
		self.backend = None
		self.kind = ""
		try:
			from paddleocr import PaddleOCR  # type: ignore
			self.backend = PaddleOCR(use_angle_cls=True, lang='en')
			self.kind = "paddle"
		except Exception:
			try:
				import easyocr  # type: ignore
				self.backend = easyocr.Reader(['en'], gpu=False)
				self.kind = "easyocr"
			except Exception:
				try:
					import pytesseract  # type: ignore
					self.backend = pytesseract
					self.kind = "tesseract"
				except Exception:
					self.backend = None
					self.kind = "none"

	def _pdf_to_images(self, data: bytes) -> List[Image.Image]:
		try:
			import pdf2image  # type: ignore
		except Exception:
			return []
		try:
			pages = pdf2image.convert_from_bytes(data, dpi=300)
			return pages
		except Exception:
			return []

	def _pdf_to_text(self, data: bytes) -> str:
		# Native text extraction using PyPDF2; returns empty if not extractable
		try:
			from PyPDF2 import PdfReader  # type: ignore
		except Exception:
			return ""
		try:
			reader = PdfReader(io.BytesIO(data))
			texts = []
			for page in reader.pages:
				try:
					texts.append(page.extract_text() or "")
				except Exception:
					continue
			return "\n".join([t for t in texts if t.strip()])
		except Exception:
			return ""

	def _preprocess(self, img: Image.Image) -> Image.Image:
		g = ImageOps.grayscale(img)
		g = g.filter(ImageFilter.SHARPEN)
		w, h = g.size
		return g.resize((int(w * 1.3), int(h * 1.3)))

	def image_bytes_to_text(self, data: bytes, filetype: str) -> str:
		if self.backend is None:
			return ""
		images: List[Image.Image] = []
		if filetype.lower() == "pdf":
			pdf_text = self._pdf_to_text(data)
			if pdf_text:
				return pdf_text
			images = self._pdf_to_images(data)
			if not images:
				return ""
		else:
			try:
				images = [Image.open(io.BytesIO(data)).convert("RGB")]
			except Exception:
				return ""

		texts: List[str] = []
		for img in images:
			proc = self._preprocess(img)
			try:
				if self.kind == "paddle":
					res = self.backend.ocr(proc, cls=True)  # type: ignore
					page_text = "\n".join([line[1][0] for line in res[0]]) if res else ""
					texts.append(page_text)
				elif self.kind == "easyocr":
					res = self.backend.readtext(proc, detail=0)  # type: ignore
					texts.append("\n".join(res))
				elif self.kind == "tesseract":
					texts.append(self.backend.image_to_string(proc, config="--oem 3 --psm 6"))  # type: ignore
				else:
					return ""
			except Exception:
				continue
		return "\n".join(texts)


# Lightweight regex-based extraction with optional OpenAI refinement
FIELDS = ["vendor", "date", "total", "currency", "po_number"]

_date_re = re.compile(r"(\b\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}\b|\b\d{4}[\-/]\d{1,2}[\-/]\d{1,2}\b)")
_money_re = re.compile(r"([A-Z]{3})?\s?\$?\s?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})|[0-9]+\.[0-9]{2})")
_po_re = re.compile(r"(?:Purchase\s+Order\s+Number|PO\s*#?)\s*[:\s]+([A-Z0-9\-]+)", re.I)
_invnum_re = re.compile(r"Invoice\s*Number\s*[:\s]+([A-Z0-9\-]+)", re.I)
_id_validate_re = re.compile(r"[A-Z]{2,}-\d{6,}|\d{8,}")


def extract_fields(text: str, use_openai: bool = False, model: str = "gpt-4o-mini") -> dict:
	data = {k: None for k in FIELDS}
	lines = [l.strip() for l in text.splitlines() if l.strip()]
	if lines:
		data["vendor"] = lines[0][:64]
	m = _date_re.search(text)
	if m:
		data["date"] = m.group(1)
	# Try Invoice Number first, then PO
	m = _invnum_re.search(text)
	if not m:
		m = _po_re.search(text)
	if m:
		id_val = m.group(1).strip()
		# Only accept if it looks like a valid ID (has digits)
		if _id_validate_re.search(id_val) or len(re.findall(r'\d', id_val)) >= 6:
			data["po_number"] = id_val
	m = _money_re.findall(text)
	if m:
		currency = next((c for c, _ in m if c), None)
		amount = m[-1][1]
		data["currency"] = currency or ""
		data["total"] = amount

	if not use_openai:
		return data

	try:
		from openai import OpenAI  # type: ignore
		client = OpenAI()
		prompt = (
			"Extract vendor, date, currency, total, po_number from the text. "
			"Return pure JSON with keys vendor,date,currency,total,po_number."
		)
		resp = client.chat.completions.create(
			model=model,
			messages=[{"role": "user", "content": prompt + "\n\n" + text[:6000]}],
			temperature=0,
		)
		content = resp.choices[0].message.content or "{}"
		import json
		refined = json.loads(content)
		for k in FIELDS:
			if refined.get(k):
				data[k] = refined.get(k)
		return data
	except Exception:
		return data
