import streamlit as st
from lib.db import get_pipeline_stages, save_pipeline_stages

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
st.title("Settings")

# ── Pipeline Stages ────────────────────────────────────────────────────────────
st.subheader("Hiring Pipeline Stages")
st.caption("Customize the stages candidates move through. First stage is always the starting point. 'Hired' and 'Rejected' must be kept as final stages.")

current_stages = get_pipeline_stages()

if "pipeline_stages_edit" not in st.session_state:
    st.session_state["pipeline_stages_edit"] = list(current_stages)

stages = st.session_state["pipeline_stages_edit"]

# Render each stage as an editable row
to_delete = None
for i, stage in enumerate(stages):
    col_num, col_input, col_del = st.columns([0.3, 3, 0.5])
    with col_num:
        st.markdown(f"**{i + 1}.**")
    with col_input:
        updated = st.text_input(
            f"Stage {i + 1}",
            value=stage,
            key=f"stage_input_{i}",
            label_visibility="collapsed",
        )
        stages[i] = updated
    with col_del:
        # Protect Hired and Rejected from deletion
        is_protected = stage.lower() in ("hired", "rejected")
        if not is_protected:
            if st.button("✕", key=f"del_stage_{i}"):
                to_delete = i

if to_delete is not None:
    stages.pop(to_delete)
    st.session_state["pipeline_stages_edit"] = stages
    st.rerun()

# Add new stage (inserted before Hired/Rejected)
if st.button("＋ Add Stage"):
    # Insert before the last two (Hired, Rejected)
    insert_at = max(len(stages) - 2, 1)
    stages.insert(insert_at, "New Stage")
    st.session_state["pipeline_stages_edit"] = stages
    st.rerun()

st.divider()

col_save, col_reset = st.columns(2)
with col_save:
    if st.button("Save Pipeline", type="primary"):
        # Validate: must have at least 2 stages and end with Hired/Rejected
        names = [s.strip() for s in stages if s.strip()]
        if len(names) < 2:
            st.error("You need at least 2 stages.")
        else:
            save_pipeline_stages(names)
            st.session_state["pipeline_stages_edit"] = names
            st.success("Pipeline saved!")

with col_reset:
    if st.button("Reset to Default"):
        defaults = ["Shortlisted", "Reviewing", "Interview Round 1", "Interview Round 2", "Hired", "Rejected"]
        save_pipeline_stages(defaults)
        st.session_state["pipeline_stages_edit"] = defaults
        st.rerun()
