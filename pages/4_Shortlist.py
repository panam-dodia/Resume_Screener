import streamlit as st
from lib.db import list_shortlist_roles, list_shortlisted, update_shortlist, remove_from_shortlist

st.set_page_config(page_title="Shortlisted Candidates", page_icon="⭐", layout="wide")
st.title("Shortlisted Candidates")

STATUSES = ["Shortlisted", "Reviewing", "Interview", "Hired", "Rejected"]

STATUS_ICON = {
    "Shortlisted": "🔵",
    "Reviewing":   "🟡",
    "Interview":   "🟠",
    "Hired":       "🟢",
    "Rejected":    "🔴",
}

# ── Role filter ───────────────────────────────────────────────────────────────
roles = list_shortlist_roles()

if not roles:
    st.info("No candidates shortlisted yet. Go to **Search Candidates**, check candidates, and click **Shortlist Selected**.")
    st.stop()

role_options = ["All roles"] + roles
selected_role = st.selectbox("Filter by role", options=role_options)

role_filter = None if selected_role == "All roles" else selected_role

# ── Load candidates ───────────────────────────────────────────────────────────
candidates = list_shortlisted(role_filter=role_filter)

if not candidates:
    st.info("No candidates found for this role.")
    st.stop()

# Group by role for display
from collections import defaultdict
by_role: dict[str, list] = defaultdict(list)
for c in candidates:
    by_role[c["role_name"]].append(c)

# ── Render each role group ────────────────────────────────────────────────────
for role, entries in by_role.items():
    st.markdown(f"## {role}  `{len(entries)} candidate{'s' if len(entries) != 1 else ''}`")

    for entry in entries:
        shortlist_id = entry["id"]
        name = entry.get("candidate_name") or "Unknown"
        file_name = entry.get("file_name", "")
        batch = entry.get("batch_name", "")
        current_status = entry.get("status", "Shortlisted")
        current_notes = entry.get("notes", "") or ""
        icon = STATUS_ICON.get(current_status, "⚪")

        with st.container(border=True):
            live_status = st.session_state.get(f"status_{shortlist_id}", current_status)
            live_icon = STATUS_ICON.get(live_status, "⚪")

            col_name, col_status = st.columns([3, 1])
            with col_name:
                st.markdown(f"**{name}**")
                st.caption(f"{file_name} · Batch: {batch}")
            with col_status:
                st.markdown(f"### {live_icon} {live_status}")

            col_select, col_notes, col_actions = st.columns([1, 2, 1])

            with col_select:
                new_status = st.selectbox(
                    "Status",
                    options=STATUSES,
                    index=STATUSES.index(current_status),
                    key=f"status_{shortlist_id}",
                    label_visibility="collapsed",
                )

            with col_notes:
                new_notes = st.text_input(
                    "Notes",
                    value=current_notes,
                    placeholder="Add notes...",
                    key=f"notes_{shortlist_id}",
                    label_visibility="collapsed",
                )

            with col_actions:
                col_save, col_remove = st.columns(2)
                with col_save:
                    if st.button("Save", key=f"save_{shortlist_id}", type="primary"):
                        update_shortlist(shortlist_id, new_status, new_notes)
                        st.rerun()
                with col_remove:
                    if st.button("Remove", key=f"remove_{shortlist_id}"):
                        remove_from_shortlist(shortlist_id)
                        st.rerun()

    st.divider()
