import streamlit as st
from collections import defaultdict
from lib.db import (
    list_shortlist_roles, list_shortlisted, update_shortlist,
    remove_from_shortlist, get_pipeline_stages, get_rejection_candidates,
    update_resume_email, delete_resume,
)
from lib.storage import delete_pdf
from lib.email_sender import (
    send_hired_email, send_rejection_email, send_interview_email, interview_template,
)

st.set_page_config(page_title="Shortlisted Candidates", page_icon="⭐", layout="wide")
st.title("Shortlisted Candidates")

# Load dynamic pipeline stages from DB
STAGES = get_pipeline_stages()
if not STAGES:
    STAGES = ["Shortlisted", "Reviewing", "Interview Round 1", "Hired", "Rejected"]

INTERVIEW_STAGES = [s for s in STAGES if s.lower().startswith("interview")]
HIRED_STAGE = next((s for s in STAGES if s.lower() == "hired"), "Hired")
REJECTED_STAGE = next((s for s in STAGES if s.lower() == "rejected"), "Rejected")

STATUS_ICON = {}
for s in STAGES:
    sl = s.lower()
    if sl == "hired":
        STATUS_ICON[s] = "🟢"
    elif sl == "rejected":
        STATUS_ICON[s] = "🔴"
    elif sl.startswith("interview"):
        STATUS_ICON[s] = "🟠"
    elif sl == "reviewing":
        STATUS_ICON[s] = "🟡"
    else:
        STATUS_ICON[s] = "🔵"

# ── Role filter ────────────────────────────────────────────────────────────────
roles = list_shortlist_roles()

if not roles:
    st.info("No candidates shortlisted yet. Go to **Search Candidates** and shortlist candidates.")
    st.stop()

role_options = ["All roles"] + roles
selected_role = st.selectbox("Filter by role", options=role_options)
role_filter = None if selected_role == "All roles" else selected_role

candidates = list_shortlisted(role_filter=role_filter)

if not candidates:
    st.info("No candidates found for this role.")
    st.stop()

by_role: dict[str, list] = defaultdict(list)
for c in candidates:
    by_role[c["role_name"]].append(c)

# ── Render each role group ─────────────────────────────────────────────────────
for role, entries in by_role.items():
    st.markdown(f"## {role}  `{len(entries)} candidate{'s' if len(entries) != 1 else ''}`")

    for entry in entries:
        shortlist_id = entry["id"]
        name = entry.get("candidate_name") or "Unknown"
        first_name = name.split()[0] if name != "Unknown" else name
        file_name = entry.get("file_name", "")
        batch = entry.get("batch_name", "")
        email = entry.get("email")
        current_status = entry.get("status", STAGES[0])
        current_notes = entry.get("notes", "") or ""

        with st.container(border=True):
            live_status = st.session_state.get(f"status_{shortlist_id}", current_status)
            live_icon = STATUS_ICON.get(live_status, "⚪")

            col_name, col_status = st.columns([3, 1])
            with col_name:
                st.markdown(f"**{name}**")
                if email:
                    st.caption(f"{file_name} · Batch: {batch} · {email}")
                else:
                    st.caption(f"{file_name} · Batch: {batch}")
                    col_email_input, col_email_save = st.columns([3, 1])
                    with col_email_input:
                        manual_email = st.text_input(
                            "Email",
                            placeholder="Enter email manually...",
                            key=f"manual_email_{shortlist_id}",
                            label_visibility="collapsed",
                        )
                    with col_email_save:
                        if st.button("Save Email", key=f"save_email_{shortlist_id}"):
                            if manual_email and "@" in manual_email:
                                update_resume_email(entry["resume_id"], manual_email)
                                st.success("Email saved.")
                                st.rerun()
                            else:
                                st.error("Invalid email.")
            with col_status:
                st.markdown(f"### {live_icon} {live_status}")

            col_select, col_notes, col_actions = st.columns([1, 2, 1])

            with col_select:
                stage_index = STAGES.index(current_status) if current_status in STAGES else 0
                new_status = st.selectbox(
                    "Status",
                    options=STAGES,
                    index=stage_index,
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
                col_save, col_remove, col_delete = st.columns(3)
                with col_save:
                    if st.button("Save", key=f"save_{shortlist_id}", type="primary"):
                        update_shortlist(shortlist_id, new_status, new_notes)
                        st.rerun()
                with col_remove:
                    if st.button("Remove", key=f"remove_{shortlist_id}", help="Remove from shortlist only"):
                        remove_from_shortlist(shortlist_id)
                        st.rerun()
                with col_delete:
                    if st.button("🗑️", key=f"delete_{shortlist_id}", help="Delete candidate from database"):
                        st.session_state[f"confirm_delete_{shortlist_id}"] = True

            # ── Delete confirmation ────────────────────────────────────────
            if st.session_state.get(f"confirm_delete_{shortlist_id}"):
                st.warning(f"Permanently delete **{name}**'s resume from the database? This cannot be undone.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes, Delete", key=f"yes_delete_{shortlist_id}", type="primary"):
                        storage_path = delete_resume(entry["resume_id"])
                        if storage_path:
                            delete_pdf(storage_path)
                        st.session_state.pop(f"confirm_delete_{shortlist_id}", None)
                        st.rerun()
                with col_no:
                    if st.button("Cancel", key=f"cancel_delete_{shortlist_id}"):
                        st.session_state.pop(f"confirm_delete_{shortlist_id}", None)
                        st.rerun()

            # ── Email action buttons based on current status ───────────────
            if current_status == HIRED_STAGE:
                col_hired, col_reject = st.columns(2)
                with col_hired:
                    if st.button("📧 Send Hired Email", key=f"btn_hired_{shortlist_id}", type="primary"):
                        if email:
                            try:
                                send_hired_email(email, first_name, role)
                                st.success(f"Hired email sent to {email}")
                            except Exception as e:
                                st.error(f"Failed: {e}")
                        else:
                            st.warning("Save an email address first.")
                with col_reject:
                    if st.button("📧 Send Rejections", key=f"btn_reject_{shortlist_id}"):
                        others = get_rejection_candidates(role, shortlist_id)
                        st.session_state[f"show_rejection_confirm_{shortlist_id}"] = others
                        st.rerun()

            elif current_status in INTERVIEW_STAGES:
                if st.button("📧 Send Interview Email", key=f"btn_interview_{shortlist_id}", type="primary"):
                    _, default_body = interview_template(first_name, role)
                    st.session_state[f"show_interview_email_{shortlist_id}"] = True
                    st.session_state[f"interview_body_{shortlist_id}"] = default_body

            # ── Interview email editor ─────────────────────────────────────
            if st.session_state.get(f"show_interview_email_{shortlist_id}"):
                st.markdown("**Send Interview Invitation**")
                body = st.text_area(
                    "Email body (editable)",
                    value=st.session_state.get(f"interview_body_{shortlist_id}", ""),
                    height=200,
                    key=f"interview_body_input_{shortlist_id}",
                )
                col_send, col_skip = st.columns(2)
                with col_send:
                    if st.button("Send Email", key=f"send_interview_{shortlist_id}", type="primary"):
                        if email:
                            try:
                                send_interview_email(email, first_name, role, body)
                                st.success(f"Interview invitation sent to {email}")
                            except Exception as e:
                                st.error(f"Failed to send: {e}")
                        else:
                            st.warning("No email found for this candidate — cannot send.")
                        del st.session_state[f"show_interview_email_{shortlist_id}"]
                with col_skip:
                    if st.button("Skip", key=f"skip_interview_{shortlist_id}"):
                        del st.session_state[f"show_interview_email_{shortlist_id}"]

            # ── Rejection confirmation after Hired ─────────────────────────
            rejection_candidates = st.session_state.get(f"show_rejection_confirm_{shortlist_id}")
            if rejection_candidates is not None:
                st.markdown("**Send rejection emails to remaining candidates?**")
                for other in rejection_candidates:
                    oname = other.get("candidate_name", "Unknown")
                    oemail = other.get("email")
                    if oemail:
                        st.markdown(f"- {oname} — {oemail}")
                    else:
                        st.markdown(f"- {oname} — ⚠️ Email not found (will be skipped)")

                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Send Rejections", key=f"confirm_reject_{shortlist_id}", type="primary"):
                        sent, skipped = 0, 0
                        for other in rejection_candidates:
                            oemail = other.get("email")
                            oname = other.get("candidate_name", "Unknown")
                            ofirst = oname.split()[0]
                            oid = other.get("id")
                            if oemail:
                                try:
                                    send_rejection_email(oemail, ofirst, role)
                                    update_shortlist(oid, REJECTED_STAGE, "Auto-rejected after hire")
                                    sent += 1
                                except Exception:
                                    skipped += 1
                            else:
                                skipped += 1
                        st.success(f"Sent {sent} rejection email(s). Skipped {skipped} (no email).")
                        del st.session_state[f"show_rejection_confirm_{shortlist_id}"]
                        st.rerun()
                with col_no:
                    if st.button("Skip", key=f"skip_reject_{shortlist_id}"):
                        del st.session_state[f"show_rejection_confirm_{shortlist_id}"]

    st.divider()
