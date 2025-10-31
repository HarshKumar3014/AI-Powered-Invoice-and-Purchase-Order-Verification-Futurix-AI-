from __future__ import annotations
import io
from typing import Dict, Any, Tuple
import streamlit as st
import pandas as pd
from PIL import Image

# Minimal, reusable UI components

def render_header() -> None:
	st.set_page_config(page_title="Futurix AI - Invoice/PO Verification", layout="wide")
	# Enhanced professional styling
	st.markdown(
		"""
		<style>
			/* Main content area */
			section.main > div {padding-top: 1rem;}
			.block-container {padding-top: 2rem; max-width: 1400px;}
			
			/* Header styling */
			[data-testid="stHeader"] {
				background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
				border-bottom: 1px solid rgba(255,255,255,0.1);
			}
			
			/* Sidebar - clean, minimal, matches theme */
			[data-testid="stSidebar"] {
				background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
				color: #ffffff;
			}
			[data-testid="stSidebar"] * {
				color: #e5e7eb !important;
			}
			[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
				color: #ffffff !important;
				border-bottom: 2px solid #667eea;
				padding-bottom: 0.5rem;
			}
			[data-testid="stSidebar"] label {
				color: #d1d5db !important;
			}
			[data-testid="stSidebar"] .stSelectbox label,
			[data-testid="stSidebar"] .stCheckbox label {
				color: #e5e7eb !important;
			}
			
			/* Tables */
			.dataframe td, .dataframe th {
				font-size: 0.95rem;
				border: 1px solid #e0e0e0;
			}
			
			/* File uploaders */
			.stFileUploader > div > div {
				background-color: #f8f9fa;
				border-radius: 8px;
				padding: 1rem;
				border: 2px dashed #cbd5e1;
			}
			
			/* Typography */
			h1 {
				color: #1f2937;
				font-weight: 700;
				margin-bottom: 0.5rem;
			}
			h2 {
				color: #374151;
				border-bottom: 2px solid #667eea;
				padding-bottom: 0.5rem;
				margin-top: 2rem;
			}
			h3 {
				color: #374151;
				border-bottom: 2px solid #667eea;
				padding-bottom: 0.5rem;
			}
			
			/* Buttons */
			.stButton > button {
				border-radius: 6px;
				font-weight: 600;
				transition: all 0.3s;
			}
			
			/* Metrics */
			.stMetric {
				background-color: #f8f9fa;
				padding: 1rem;
				border-radius: 8px;
				border-left: 4px solid #667eea;
			}
			.element-container:has(> div[data-testid="stMetric"]) {
				padding: 0.5rem;
			}
			
			/* Remove empty space */
			.css-1d391kg {padding-top: 1.5rem;}
			div[data-testid="stSidebarContent"] {
				padding-top: 2rem;
			}
		</style>
		""",
		unsafe_allow_html=True,
	)
	st.title("🤖 AI-Powered Invoice and Purchase Order Verification")
	st.caption("Futurix AI · Enterprise-Ready Verification System")


def _show_preview(file_bytes: bytes, filename: str, label: str) -> None:
	if not file_bytes:
		return
	st.markdown(f"**{label} Preview**")
	file_ext = filename.split('.')[-1].lower() if '.' in filename else ""
	if file_ext in ["png", "jpg", "jpeg"]:
		try:
			img = Image.open(io.BytesIO(file_bytes))
			st.image(img, use_container_width=True, caption=filename)
		except Exception:
			st.caption(f"Preview unavailable for {filename}")
	elif file_ext == "pdf":
		try:
			from pdf2image import convert_from_bytes
			pages = convert_from_bytes(file_bytes, first_page=1, last_page=1, dpi=150)
			if pages:
				st.image(pages[0], use_container_width=True, caption=f"{filename} (Page 1)")
		except Exception:
			st.caption(f"PDF preview requires poppler. File: {filename}")


def upload_pair() -> Tuple[bytes | None, bytes | None]:
	col1, col2 = st.columns(2, gap="large")
	inv_bytes = po_bytes = None
	with col1:
		inv = st.file_uploader("📄 Upload Invoice (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"], key="invoice")
		if inv is not None:
			inv_bytes = inv.read()
			st.markdown("---")
			_show_preview(inv_bytes, inv.name, "Invoice")
	with col2:
		po = st.file_uploader("📋 Upload Purchase Order (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"], key="po")
		if po is not None:
			po_bytes = po.read()
			st.markdown("---")
			_show_preview(po_bytes, po.name, "Purchase Order")
	return inv_bytes, po_bytes


def show_extraction(extracted: Dict[str, Any], title: str) -> None:
	st.subheader(title)
	# Display as a clean table format
	if extracted:
		field_labels = {
			"vendor": "Vendor", 
			"date": "Date", 
			"total": "Total", 
			"currency": "Currency", 
			"po_number": "PO/Invoice #"
		}
		data_rows = []
		for key, label in field_labels.items():
			val = extracted.get(key)
			display_val = str(val)[:50] if val and str(val).strip() and str(val).strip().lower() != "none" else "—"
			data_rows.append({"Field": label, "Value": display_val})
		if data_rows:
			df_extract = pd.DataFrame(data_rows)
			st.dataframe(df_extract, use_container_width=True, hide_index=True)
	with st.expander("📋 View Full Extraction Details"):
		st.json(extracted)
	# Show raw text preview if provided in dict under _raw
	raw = extracted.get("_raw") if isinstance(extracted, dict) else None
	if raw:
		with st.expander("🔍 Raw OCR Text (Preview)"):
			st.code(str(raw)[:1000])


def show_comparison(df: pd.DataFrame) -> None:
	st.subheader("📊 Field Comparison Results")
	if df.empty:
		st.warning("⚠️ No fields available for comparison. Extraction may have failed.")
		return
	
	def _row_style(r: pd.Series) -> list[str]:
		status = str(r.get("status", ""))
		bg = ""
		fg = ""
		if status == "mismatch":
			bg, fg = "#ff4d4f", "#ffffff"  # vivid red
		elif status == "match":
			bg, fg = "#52c41a", "#000000"  # green
		elif status == "missing":
			bg, fg = "#faad14", "#000000"  # amber
		style = f"background-color:{bg};color:{fg};font-weight:500" if bg else ""
		return [style for _ in r]
	
	try:
		styled = df.style.apply(_row_style, axis=1)
		st.dataframe(styled, use_container_width=True, height=400)
	except Exception:
		st.dataframe(df, use_container_width=True, height=400)


def csv_download_button(df: pd.DataFrame, filename: str = "verification_results.csv") -> None:
	if df.empty:
		st.info("📄 No data available for CSV export.")
		return
	csv_buf = io.StringIO()
	df.to_csv(csv_buf, index=False)
	st.download_button(
		"📥 Download Comparison CSV",
		data=csv_buf.getvalue(),
		file_name=filename,
		mime="text/csv",
		type="primary"
	)
