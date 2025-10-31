from __future__ import annotations
from typing import Dict, Any, Tuple, Set
import pandas as pd
import re

FIELDS = ["vendor", "date", "currency", "total", "po_number"]

# Flexible mapping: accept many possible keys and fallback to regex on raw text
SYNONYMS = {
	"vendor": ["vendor", "seller", "supplier", "from"],
	"date": ["date", "date of issue", "invoice date", "date issued"],
	"currency": ["currency"],
	"total": ["total", "amount due", "amount", "grand total"],
	"po_number": ["po", "po number", "purchase order number", "purchase order", "invoice number", "order number"],
}

_date_re = re.compile(r"(\b\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}\b|\b\d{4}[\-/]\d{1,2}[\-/]\d{1,2}\b)")
_money_re = re.compile(r"([A-Z]{3})?\s?\$?\s?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})|[0-9]+\.[0-9]{2})")
_po_re = re.compile(r"PO\s*#?\s*([A-Z0-9\-]+)", re.I)
_inv_re = re.compile(r"Invoice\s*Number[:\s]+([A-Z0-9\-]+)", re.I)
_id_core_re = re.compile(r"(?:[A-Z]{2,}-)?(\d{6,})")
_vendor_re = re.compile(r"Vendor[:\s]+(.+)", re.I)
_seller_inline_re = re.compile(r"^(seller|vendor)\s*:\s*(.+)$", re.I | re.M)

_month_re = re.compile(
	"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2},\s+\d{4}",
	re.I,
)

_currency_symbol = {
	"$": "USD",
	"€": "EUR",
	"£": "GBP",
	"₹": "INR",
}


def _clean(s: str) -> str:
	return re.sub(r"\s+", " ", s).strip()


def _normalize_amount(text: str) -> str:
	if not text:
		return ""
	s = text.replace(",", "").replace("USD", "").replace("usd", "")
	s = re.sub(r"[^0-9\.]+", "", s)
	try:
		val = float(s)
		return f"{val:.2f}"
	except Exception:
		return ""


def _normalize_company(name: str) -> str:
	s = _clean(name).lower()
	s = re.sub(r"[\.,]", "", s)
	# remove common legal suffixes
	s = re.sub(r"\b(pvt|private)\b\s*\b(ltd|limited)\b", "", s)
	s = re.sub(r"\b(incorporated|inc|llc|ltd)\b", "", s)
	s = re.sub(r"\s+", " ", s).strip()
	return s


def _normalize_record(rec: Dict[str, Any]) -> Dict[str, str]:
	if not rec:
		return {k: "" for k in FIELDS}
	lower_map = {str(k).strip().lower(): str(v) for k, v in rec.items() if v is not None}
	result: Dict[str, str] = {k: "" for k in FIELDS}
	for std, keys in SYNONYMS.items():
		for k in keys:
			if k in lower_map:
				result[std] = lower_map[k]
				break
	# Sanity cleanup for vendor label-only values
	if result["vendor"] and re.fullmatch(r"\s*(vendor|seller)\s*:?\s*", result["vendor"], re.I):
		result["vendor"] = ""
	# Validate PO/Invoice id shape; discard junk like "rt"
	if result["po_number"]:
		id_val = str(result["po_number"]).strip()
		# Must have at least 6 digits to be a valid ID
		if not (_id_core_re.search(id_val) or re.search(r"[A-Z]{2,}-\d{6,}", id_val, re.I) or re.search(r"\d{8,}", id_val)):
			result["po_number"] = ""
	# Regex fallbacks using raw text
	raw = rec.get("_raw", "")
	if raw:
		if not result["date"]:
			m = _date_re.search(raw) or _month_re.search(raw)
			if m:
				result["date"] = m.group(0)
		if not result["po_number"]:
			# Try Invoice Number first, then PO
			m = _inv_re.search(raw)
			if not m:
				m = _po_re.search(raw)
			if m:
				id_val = m.group(1).strip()
				# Extract numeric core for comparison
				core = _id_core_re.search(id_val)
				result["po_number"] = core.group(1) if core else id_val
		if not result["total"]:
			m = _money_re.findall(raw)
			if m:
				result["total"] = _normalize_amount(m[-1][1])
		if not result["currency"]:
			m = _money_re.findall(raw)
			if m:
				cur = next((c for c, _ in m if c), "")
				result["currency"] = cur
		if not result["vendor"]:
			# same-line pattern first
			m_inline = _seller_inline_re.search(raw)
			if m_inline:
				result["vendor"] = _clean(m_inline.group(2))[:64]
			if not result["vendor"]:
				# then next-line pattern
				lines = [l.rstrip() for l in raw.splitlines()]
				for idx, line in enumerate(lines):
					if line.lower().startswith("seller:") or line.lower().startswith("vendor:"):
						name = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
						if name:
							result["vendor"] = _clean(name)[:64]
							break
			if not result["vendor"]:
				m = _vendor_re.search(raw)
				if m:
					result["vendor"] = _clean(m.group(1))[:64]
	return result


def _candidate_fields(inv: Dict[str, Any], po: Dict[str, Any]) -> Set[str]:
	keys: Set[str] = set(FIELDS)
	for rec in (inv or {}, po or {}):
		for k in rec.keys():
			lk = str(k).strip().lower()
			if lk and lk != "_raw":
				keys.add(lk)
	return keys


def _resolve(rec: Dict[str, Any], std_field: str, normalized: Dict[str, str]) -> str:
	# Prefer normalized when available
	val = (normalized.get(std_field) or "").strip()
	if val:
		return val
	# Otherwise consider raw with sanity checks for important fields
	raw_val = (rec.get(std_field) if rec else None)
	if raw_val is None:
		return ""
	s = str(raw_val).strip()
	if not s:
		return ""
	if std_field == "vendor":
		# discard label-only
		if re.fullmatch(r"\s*(vendor|seller)\s*:?\s*", s, re.I):
			return ""
		return s
	if std_field == "po_number":
		core = _id_core_re.search(s)
		return core.group(1) if core else ""
	return s


def compare_records(inv: Dict[str, Any], po: Dict[str, Any]) -> Tuple[pd.DataFrame, int]:
	inv_n = _normalize_record(inv)
	po_n = _normalize_record(po)
	rows = []
	mismatches = 0
	for f in sorted(_candidate_fields(inv, po)):
		iv = _resolve(inv, f, inv_n)
		pv = _resolve(po, f, po_n)
		# skip fields entirely empty on both sides
		if not iv and not pv:
			continue
		status = ""
		# Numeric compare for totals with tolerance
		if f in ("total",):
			ni = _normalize_amount(iv)
			np = _normalize_amount(pv)
			if ni and np:
				try:
					status = "match" if abs(float(ni) - float(np)) < 0.01 else "mismatch"
				except Exception:
					status = "mismatch"
			else:
				status = "missing"
		else:
			lv = _clean(str(iv)).lower()
			rv = _clean(str(pv)).lower()
			# company normalization for vendor
			if f in ("vendor",):
				lv = _normalize_company(lv)
				rv = _normalize_company(rv)
			# id core compare for po_number-like fields
			if f in ("po_number", "invoice number", "purchase order number", "order number"):
				li = _id_core_re.search(iv)
				ri = _id_core_re.search(pv)
				if li and ri:
					status = "match" if li.group(1) == ri.group(1) else "mismatch"
				else:
					status = "match" if lv and rv and lv == rv else ("missing" if not lv or not rv else "mismatch")
			else:
				status = "match" if lv and rv and lv == rv else ("missing" if not lv or not rv else "mismatch")
		if status == "mismatch":
			mismatches += 1
		rows.append({"field": f, "invoice": iv, "po": pv, "status": status})
	if not rows:
		return pd.DataFrame(columns=["field", "invoice", "po", "status"]), 0
	return pd.DataFrame(rows), mismatches
