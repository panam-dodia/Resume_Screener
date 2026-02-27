import os
import streamlit as st
from supabase import create_client, Client

_client: Client | None = None


def _get_secret(key: str) -> str:
    try:
        return st.secrets[key]
    except Exception:
        return os.environ[key]


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            _get_secret("SUPABASE_URL"),
            _get_secret("SUPABASE_SERVICE_KEY"),
        )
    return _client


def insert_resume(
    batch_name: str,
    candidate_name: str,
    file_name: str,
    storage_path: str,
    extracted_text: str,
    embedding: list[float],
) -> dict:
    """Insert a resume record and return the inserted row."""
    client = _get_client()
    result = (
        client.table("resumes")
        .insert(
            {
                "batch_name": batch_name,
                "candidate_name": candidate_name,
                "file_name": file_name,
                "storage_path": storage_path,
                "extracted_text": extracted_text,
                "embedding": embedding,
            }
        )
        .execute()
    )
    return result.data[0]


def get_batch_stats() -> list[dict]:
    """Return each batch with resume count and latest upload date."""
    client = _get_client()
    result = (
        client.table("resumes")
        .select("batch_name, upload_date")
        .order("upload_date", desc=True)
        .execute()
    )
    from collections import defaultdict
    stats: dict[str, dict] = {}
    for row in result.data:
        name = row["batch_name"]
        if name not in stats:
            stats[name] = {"batch_name": name, "count": 0, "latest": row["upload_date"]}
        stats[name]["count"] += 1
    return list(stats.values())


def list_batches() -> list[str]:
    """Return distinct batch names ordered by most recent upload first."""
    client = _get_client()
    result = (
        client.table("resumes")
        .select("batch_name, upload_date")
        .order("upload_date", desc=True)
        .execute()
    )
    seen = set()
    batches = []
    for row in result.data:
        name = row["batch_name"]
        if name not in seen:
            seen.add(name)
            batches.append(name)
    return batches


def search_by_embedding(
    query_embedding: list[float],
    batch_filter: list[str] | None = None,
    limit: int = 20,
) -> list[dict]:
    """
    Find the most semantically similar resumes to the query embedding.
    Optionally filter to specific batches.
    Returns up to `limit` rows ordered by cosine similarity.
    """
    client = _get_client()

    # Use Supabase RPC to call our pgvector similarity search function
    params = {
        "query_embedding": query_embedding,
        "match_count": limit,
        "batch_names": batch_filter if batch_filter else [],
    }
    result = client.rpc("search_resumes", params).execute()
    return result.data


def get_resume_by_id(resume_id: str) -> dict | None:
    """Fetch a single resume by its UUID."""
    client = _get_client()
    result = (
        client.table("resumes")
        .select("*")
        .eq("id", resume_id)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None


# ── Shortlist / Pipeline functions ────────────────────────────────────────────

def shortlist_candidates(resume_ids: list[str], role_name: str) -> int:
    """
    Bulk-add candidates to the shortlist for a given role.
    Skips duplicates (same resume + role already shortlisted).
    Returns the number of newly added rows.
    """
    client = _get_client()

    # Fetch existing entries for this role to avoid duplicates
    existing = (
        client.table("shortlists")
        .select("resume_id")
        .eq("role_name", role_name)
        .in_("resume_id", resume_ids)
        .execute()
    )
    already = {row["resume_id"] for row in existing.data}
    new_ids = [rid for rid in resume_ids if rid not in already]

    if not new_ids:
        return 0

    rows = [{"resume_id": rid, "role_name": role_name} for rid in new_ids]
    client.table("shortlists").insert(rows).execute()
    return len(new_ids)


def list_shortlisted(role_filter: str | None = None) -> list[dict]:
    """
    Return shortlisted candidates joined with their resume data.
    Optionally filter to a specific role.
    Each row contains shortlist fields + resume fields (name, file_name, batch_name).
    """
    client = _get_client()
    query = client.table("shortlists").select(
        "id, role_name, status, notes, shortlisted_at, "
        "resume_id, resumes(candidate_name, file_name, batch_name, storage_path)"
    ).order("shortlisted_at", desc=True)

    if role_filter:
        query = query.eq("role_name", role_filter)

    result = query.execute()
    # Flatten nested resume data for easier use in UI
    rows = []
    for row in result.data:
        resume = row.pop("resumes", {}) or {}
        rows.append({**row, **resume})
    return rows


def list_shortlist_roles() -> list[str]:
    """Return distinct role names ordered by most recent shortlist entry."""
    client = _get_client()
    result = (
        client.table("shortlists")
        .select("role_name, shortlisted_at")
        .order("shortlisted_at", desc=True)
        .execute()
    )
    seen = set()
    roles = []
    for row in result.data:
        name = row["role_name"]
        if name not in seen:
            seen.add(name)
            roles.append(name)
    return roles


def update_shortlist(shortlist_id: str, status: str, notes: str) -> dict:
    """Update status and notes for a shortlist entry."""
    client = _get_client()
    result = (
        client.table("shortlists")
        .update({"status": status, "notes": notes})
        .eq("id", shortlist_id)
        .execute()
    )
    return result.data[0] if result.data else {}


def remove_from_shortlist(shortlist_id: str):
    """Delete a shortlist entry."""
    client = _get_client()
    client.table("shortlists").delete().eq("id", shortlist_id).execute()
