import streamlit as st
from lib.db import list_batches, search_by_embedding, shortlist_candidates
from lib.ai import get_embedding, score_candidates
from lib.storage import get_signed_url

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
    st.session_state.pop("search_results", None)
    st.session_state.pop("search_candidate_map", None)

    with st.spinner("Searching resumes..."):
        query_embedding = get_embedding(query)
        candidates = search_by_embedding(
            query_embedding=query_embedding,
            batch_filter=batch_filter,
            limit=20,
        )

    if not candidates:
        st.warning("No matching resumes found. Try a different query or check that resumes have been uploaded.")
        st.stop()

    with st.spinner(f"Scoring {len(candidates)} candidates with Gemini..."):
        scored = score_candidates(query, candidates)

    st.session_state["search_results"] = scored
    st.session_state["search_candidate_map"] = {c["id"]: c for c in candidates}

# ── Render results ─────────────────────────────────────────────────────────────
if "search_results" in st.session_state:
    scored = st.session_state["search_results"]
    candidate_map = st.session_state["search_candidate_map"]

    # ── Role name input — set once at the top, used by every Shortlist button ──
    col_label, col_role_input = st.columns([1, 3])
    with col_label:
        st.markdown("**Shortlist role:**")
    with col_role_input:
        shortlist_role = st.text_input(
            "Role name",
            placeholder="e.g. ML Engineer Feb 2026",
            label_visibility="collapsed",
            key="shortlist_role_input",
        )

    st.markdown(f"### Top {len(scored)} Results")

    for rank, result in enumerate(scored, start=1):
        candidate_id = result.get("id")
        score = result.get("score", 0)
        summary = result.get("summary", "")
        match_reason = result.get("match_reason", result.get("reason", ""))
        gaps = result.get("gaps", "")
        candidate = candidate_map.get(candidate_id, {})
        name = candidate.get("candidate_name", "Unknown")
        batch = candidate.get("batch_name", "")
        file_name = candidate.get("file_name", "")

        if score >= 80:
            badge = f"🟢 {score}/100"
        elif score >= 60:
            badge = f"🟡 {score}/100"
        else:
            badge = f"🔴 {score}/100"

        with st.container(border=True):
            col_name, col_score, col_btn = st.columns([3, 1, 1])
            with col_name:
                st.markdown(f"**{rank}. {name}**")
                st.caption(f"{file_name} · Batch: {batch}")
            with col_score:
                st.markdown(f"### {badge}")
            with col_btn:
                already_added = st.session_state.get(f"shortlisted_{candidate_id}")
                if already_added:
                    st.success("Shortlisted")
                elif st.button(
                    "Shortlist",
                    key=f"sl_{candidate_id}",
                    disabled=not shortlist_role.strip(),
                    help="Set a role name above first" if not shortlist_role.strip() else "",
                ):
                    added = shortlist_candidates([candidate_id], shortlist_role.strip())
                    st.session_state[f"shortlisted_{candidate_id}"] = True
                    if added > 0:
                        st.rerun()

            if summary:
                st.markdown(f"*{summary}*")

            if match_reason:
                st.markdown(f"**Why it matches:** {match_reason}")

            if gaps and gaps.lower() != "none":
                st.markdown(f"**Gap:** {gaps}")

            with st.expander("View Resume"):
                try:
                    signed_url = get_signed_url(candidate.get("storage_path", ""))
                    st.link_button("Download Original PDF", signed_url, icon="⬇️")
                except Exception:
                    pass
                st.text_area(
                    label="Extracted Text",
                    value=candidate.get("extracted_text", ""),
                    height=400,
                    label_visibility="collapsed",
                    key=f"text_{candidate_id}",
                )
