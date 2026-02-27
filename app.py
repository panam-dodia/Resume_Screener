import streamlit as st

st.set_page_config(
    page_title="Resume Screener",
    page_icon="📋",
    layout="wide",
)

st.title("Resume Screener")
st.markdown(
    """
    **Upload once. Query anytime.**

    Use the sidebar to navigate:

    - **Upload Resumes** — Upload a batch of PDFs. Text is extracted and stored automatically.
    - **Search Candidates** — Ask any question or paste a job description. Get scored results with links back to source resumes.
    - **View Resume** — Open an individual resume (navigated to from search results).

    ---
    """
)

col1, col2 = st.columns(2)
with col1:
    st.info("**New batch?** Go to Upload Resumes in the sidebar.")
with col2:
    st.info("**Ready to search?** Go to Search Candidates in the sidebar.")
