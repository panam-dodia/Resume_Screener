import streamlit as st
from supabase import create_client, Client

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_SERVICE_KEY"],
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
