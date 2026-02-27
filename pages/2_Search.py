import streamlit as st
from lib.db import list_batches, search_by_embedding
from lib.ai import get_embedding, score_candidates

st.set_page_config(page_title="Search Candidates", page_icon="🔍", layout="wide")
st.title("Search Candidates")

# ── Batch selector ────────────────────────────────────────────────────────────
batches = list_batches()

if not batches:
    st.info("No resumes uploaded yet. Go to **Upload Resumes** to get started.")
    st.stop()

batch_options = ["All batches"] + batches
selected = st.multiselect(
    "Filter by batch (leave blank = search all)",
    options=batch_options,
    default=["All batches"],
)

batch_filter = None
if selected and "All batches" not in selected:
    batch_filter = selected

# ── Query input ───────────────────────────────────────────────────────────────
query = st.text_area(
    "Job description or question",
    placeholder="e.g. Senior Python engineer with experience in machine learning and distributed systems",
    height=120,
)

if st.button("Search", type="primary", disabled=not query.strip()):
    with st.spinner("Searching resumes..."):
        # 1. Embed the query
        query_embedding = get_embedding(query)

        # 2. Vector search in DB
        candidates = search_by_embedding(
            query_embedding=query_embedding,
            batch_filter=batch_filter,
            limit=20,
        )

    if not candidates:
        st.warning("No matching resumes found. Try a different query or check that resumes have been uploaded.")
        st.stop()

    with st.spinner(f"Scoring {len(candidates)} candidates with Gemini..."):
        # 3. Ask Gemini to score and explain each candidate
        scored = score_candidates(query, candidates)

    # ── Results ───────────────────────────────────────────────────────────────
    # Build a lookup so we can display batch info alongside scores
    candidate_map = {c["id"]: c for c in candidates}

    st.markdown(f"### Top {len(scored)} Results")

    for rank, result in enumerate(scored, start=1):
        candidate_id = result.get("id")
        score = result.get("score", 0)
        reason = result.get("reason", "")
        candidate = candidate_map.get(candidate_id, {})
        name = candidate.get("candidate_name", "Unknown")
        batch = candidate.get("batch_name", "")

        # Color-code the score badge
        if score >= 80:
            badge = f"🟢 {score}/100"
        elif score >= 60:
            badge = f"🟡 {score}/100"
        else:
            badge = f"🔴 {score}/100"

        with st.container(border=True):
            col_name, col_score = st.columns([3, 1])
            with col_name:
                st.markdown(f"**{rank}. {name}**")
                st.caption(f"Batch: {batch}")
            with col_score:
                st.markdown(f"### {badge}")

            st.markdown(reason)

            view_url = f"/View_Resume?id={candidate_id}"
            st.page_link(view_url, label="View Resume →", icon="📄")
