import streamlit as st
from lib.db import get_resume_by_id
from lib.storage import get_signed_url

st.set_page_config(page_title="View Resume", page_icon="📄", layout="wide")

# ── Read resume ID from URL query params ─────────────────────────────────────
params = st.query_params
resume_id = params.get("id")

if not resume_id:
    st.warning("No resume selected. Go to **Search Candidates** and click 'View Resume' on a result.")
    st.stop()

resume = get_resume_by_id(resume_id)

if not resume:
    st.error(f"Resume not found (ID: {resume_id})")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.title(resume["candidate_name"] or "Unknown Candidate")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Batch", resume["batch_name"])
with col2:
    upload_date = resume.get("upload_date", "")
    if upload_date:
        upload_date = upload_date[:10]  # YYYY-MM-DD
    st.metric("Uploaded", upload_date)
with col3:
    st.metric("File", resume["file_name"])

st.divider()

# ── Download button ───────────────────────────────────────────────────────────
try:
    signed_url = get_signed_url(resume["storage_path"])
    st.link_button("Download Original PDF", signed_url, icon="⬇️")
except Exception as e:
    st.warning(f"Could not generate download link: {e}")

st.divider()

# ── Extracted text ────────────────────────────────────────────────────────────
st.subheader("Extracted Text")
st.text_area(
    label="",
    value=resume["extracted_text"],
    height=600,
    label_visibility="collapsed",
)
