import streamlit as st

home = st.Page("app_home.py", title="Home", icon="🏠", default=True)
upload = st.Page("pages/1_Upload.py", title="Upload Resumes", icon="📤")
search = st.Page("pages/2_Search.py", title="Search Candidates", icon="🔍")
shortlist = st.Page("pages/4_Shortlist.py", title="Shortlisted", icon="⭐")
database = st.Page("pages/5_Database.py", title="Database", icon="🗄️")

pg = st.navigation([home, upload, search, shortlist, database])
pg.run()
