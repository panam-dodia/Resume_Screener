import streamlit as st
from lib.db import get_batch_stats, delete_batch
from lib.storage import delete_pdf

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
    batch_name = batch["batch_name"]
    confirm_key = f"confirm_delete_batch_{batch_name}"

    with st.container(border=True):
        col_name, col_count, col_date, col_del = st.columns([3, 1, 2, 1])
        with col_name:
            st.markdown(f"**{batch_name}**")
        with col_count:
            st.markdown(f"📄 {batch['count']} resume{'s' if batch['count'] != 1 else ''}")
        with col_date:
            date_str = batch["latest"][:10] if batch["latest"] else "—"
            st.caption(f"Last upload: {date_str}")
        with col_del:
            if st.button("🗑️ Delete", key=f"del_batch_{batch_name}"):
                st.session_state[confirm_key] = True

        if st.session_state.get(confirm_key):
            st.warning(
                f"Delete **{batch_name}** and all {batch['count']} resume(s)? "
                "This also removes any shortlist entries for these candidates."
            )
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Yes, Delete", key=f"yes_delete_{batch_name}", type="primary"):
                    try:
                        paths = delete_batch(batch_name)
                        for p in paths:
                            delete_pdf(p)
                        st.session_state.pop(confirm_key, None)
                        st.success(f"Deleted batch **{batch_name}** ({len(paths)} resume(s)).")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
            with col_no:
                if st.button("Cancel", key=f"cancel_delete_{batch_name}"):
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
