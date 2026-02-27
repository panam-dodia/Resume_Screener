import json
import time
from datetime import date
import streamlit as st
from google import genai
from google.genai import types

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    return _client


def get_embedding(text: str) -> list[float]:
    """
    Generate an embedding for the given text using gemini-embedding-001.
    Text is truncated to ~8000 characters to stay within limits.
    """
    client = _get_client()
    truncated = text[:8000]
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=truncated,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    return result.embeddings[0].values


def extract_candidate_name(resume_text: str) -> str:
    """
    Ask Gemini to extract the candidate's name from the top of their resume.
    Falls back gracefully on any error.
    """
    client = _get_client()
    snippet = resume_text[:400]
    prompt = (
        "Extract the candidate's full name from the following resume text. "
        "Return ONLY the name, nothing else. If you cannot determine the name, return 'Unknown'.\n\n"
        f"Resume text:\n{snippet}"
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        name = response.text.strip()
        if len(name) > 80 or "\n" in name:
            return "Unknown"
        return name
    except Exception:
        return "Unknown"


def score_candidates(query: str, candidates: list[dict]) -> list[dict]:
    """
    Score each candidate 0-100 against the job query and explain why.
    Returns a list of dicts: [{id, score, reason}] sorted by score descending.
    """
    client = _get_client()

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

    today = date.today().strftime("%B %d, %Y")
    prompt = f"""You are a recruiter's assistant. Today's date is {today}.

For each candidate below, evaluate how well their resume matches the job description. Treat any year up to {date.today().year} as past or current experience.

Two candidates with genuinely similar backgrounds should receive similar scores — scoring must reflect actual match quality, not artificial differentiation.

JOB QUERY:
{query}

CANDIDATES:
{candidates_block}

Return a JSON array (no markdown, no extra text) with one object per candidate:
[
  {{
    "id": "<candidate UUID>",
    "score": <integer 0-100>,
    "summary": "<1 sentence describing who this candidate is, e.g. their role/specialty>",
    "match_reason": "<2-3 sentences on what specifically in this resume matches the job requirements>",
    "gaps": "<1 sentence on the biggest missing skill or gap, or 'None' if strong match>"
  }}
]

Score based on: skills alignment, relevant experience, seniority fit, and tool/tech overlap with the job description."""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
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
            err = str(e)
            if "429" in err and attempt < 2:
                wait = 60 * (attempt + 1)  # 60s, then 120s
                st.warning(f"Rate limit hit — waiting {wait}s before retry ({attempt+1}/3)...")
                time.sleep(wait)
            else:
                return [
                    {"id": c["id"], "score": 0, "reason": f"Scoring failed: {e}"}
                    for c in candidates
                ]
