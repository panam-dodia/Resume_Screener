import os
import streamlit as st
from supabase import create_client, Client

BUCKET = "resumes"

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


def upload_pdf(file_bytes: bytes, storage_path: str) -> str:
    """
    Upload a PDF to Supabase Storage.
    storage_path: e.g. "2026-02-26/john_doe_abc123.pdf"
    Returns the storage_path on success.
    """
    client = _get_client()
    client.storage.from_(BUCKET).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": "application/pdf"},
    )
    return storage_path


def get_signed_url(storage_path: str, expires: int = 3600) -> str:
    """
    Generate a temporary signed URL for downloading a PDF.
    expires: seconds until the URL expires (default 1 hour).
    """
    client = _get_client()
    result = client.storage.from_(BUCKET).create_signed_url(
        path=storage_path,
        expires_in=expires,
    )
    return result["signedURL"]
