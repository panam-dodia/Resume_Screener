import streamlit as st
from lib.db import get_batch_stats

st.set_page_config(page_title="Database", page_icon="🗄️", layout="wide")
st.title("Database")
st.caption("All resume batches currently stored.")

try:
    batches = get_batch_stats()
except Exception as e:
    st.error(f"Could not load database: {e}")
    st.stop()

if not batches:
    st.info("No resumes uploaded yet. Go to **Upload Resumes** to get started.")
    st.stop()

total_resumes = sum(b["count"] for b in batches)

col1, col2 = st.columns(2)
col1.metric("Total Batches", len(batches))
col2.metric("Total Resumes", total_resumes)

st.divider()

for batch in batches:
    with st.container(border=True):
        col_name, col_count, col_date = st.columns([3, 1, 2])
        with col_name:
            st.markdown(f"**{batch['batch_name']}**")
        with col_count:
            st.markdown(f"📄 {batch['count']} resume{'s' if batch['count'] != 1 else ''}")
        with col_date:
            date_str = batch["latest"][:10] if batch["latest"] else "—"
            st.caption(f"Last upload: {date_str}")
