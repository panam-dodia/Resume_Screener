import json
import streamlit as st
import google.generativeai as genai

_configured = False


def _configure():
    global _configured
    if not _configured:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        _configured = True


def get_embedding(text: str) -> list[float]:
    """
    Generate a 768-dimensional embedding for the given text
    using Google's text-embedding-004 model.
    Text is truncated to ~8000 characters to stay within limits.
    """
    _configure()
    truncated = text[:8000]
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=truncated,
        task_type="retrieval_document",
    )
    return result["embedding"]


def extract_candidate_name(resume_text: str) -> str:
    """
    Ask Gemini to extract the candidate's name from the top of their resume.
    Falls back gracefully on any error.
    """
    _configure()
    snippet = resume_text[:400]
    prompt = (
        "Extract the candidate's full name from the following resume text. "
        "Return ONLY the name, nothing else. If you cannot determine the name, return 'Unknown'.\n\n"
        f"Resume text:\n{snippet}"
    )
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        name = response.text.strip()
        # Sanity check: names shouldn't be very long
        if len(name) > 80 or "\n" in name:
            return "Unknown"
        return name
    except Exception:
        return "Unknown"


def score_candidates(query: str, candidates: list[dict]) -> list[dict]:
    """
    Given a job description/query and a list of candidate dicts
    (each with 'id', 'candidate_name', 'extracted_text'),
    ask Gemini to score each candidate 0-100 and explain why.

    Returns a list of dicts: [{id, score, reason}] sorted by score descending.
    """
    _configure()

    # Build a compact summary of each candidate to keep token usage manageable
    summaries = []
    for i, c in enumerate(candidates):
        text_snippet = c["extracted_text"][:1500]
        summaries.append(
            f"CANDIDATE {i+1}\n"
            f"ID: {c['id']}\n"
            f"Name: {c['candidate_name']}\n"
            f"Resume excerpt:\n{text_snippet}\n"
        )

    candidates_block = "\n---\n".join(summaries)

    prompt = f"""You are a recruiter's assistant. Score each candidate below against the job query.

JOB QUERY:
{query}

CANDIDATES:
{candidates_block}

Return a JSON array (no markdown, no extra text) with one object per candidate:
[
  {{
    "id": "<candidate UUID>",
    "score": <integer 0-100>,
    "reason": "<1-2 sentence explanation of the match>"
  }}
]

Score based on skills match, experience relevance, and seniority fit. Be honest — not every candidate will score high."""

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown code fences if Gemini adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        results = json.loads(raw)
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results
    except Exception as e:
        # Return a fallback so the UI doesn't crash
        return [
            {"id": c["id"], "score": 0, "reason": f"Scoring failed: {e}"}
            for c in candidates
        ]
