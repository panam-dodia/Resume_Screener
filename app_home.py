import streamlit as st

st.set_page_config(page_title="Resume Screener", page_icon="📋", layout="wide")

st.title("Resume Screener")
st.markdown(
    """
    **Upload once. Query anytime.**

    Use the sidebar to navigate:

    - **Upload Resumes** — Upload a batch of PDFs. Text is extracted and stored automatically.
    - **Search Candidates** — Ask any question or paste a job description. Get scored results.
    - **Shortlisted** — Track shortlisted candidates through your hiring pipeline.

    ---
    """
)

col1, col2, col3 = st.columns(3)
with col1:
    st.info("**New batch?**\nGo to Upload Resumes.")
with col2:
    st.info("**Find candidates?**\nGo to Search Candidates.")
with col3:
    st.info("**Track pipeline?**\nGo to Shortlisted.")
