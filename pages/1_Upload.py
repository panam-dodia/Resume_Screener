import uuid
import streamlit as st
from lib.pdf_parser import extract_text, extract_name_heuristic
from lib.ai import get_embedding, extract_candidate_name
from lib.storage import upload_pdf
from lib.db import insert_resume

st.set_page_config(page_title="Upload Resumes", page_icon="📤", layout="wide")
st.title("Upload Resumes")

batch_name = st.text_input(
    "Batch name",
    placeholder="e.g. 2/26/26 or Senior-Eng-Feb-2026",
    help="Give this upload a name so you can filter by it later.",
)

uploaded_files = st.file_uploader(
    "Select PDF resumes",
    type=["pdf"],
    accept_multiple_files=True,
)

if st.button("Upload & Process", type="primary", disabled=not (batch_name and uploaded_files)):
    total = len(uploaded_files)
    progress = st.progress(0, text="Starting...")
    success_count = 0
    errors = []

    for i, file in enumerate(uploaded_files):
        progress.progress((i) / total, text=f"Processing {file.name} ({i+1}/{total})...")

        try:
            pdf_bytes = file.read()

            # 1. Extract text
            text = extract_text(pdf_bytes)
            if not text.strip():
                errors.append(f"{file.name}: no text could be extracted (scanned PDF?)")
                continue

            # 2. Extract candidate name
            name = extract_candidate_name(text)
            if name == "Unknown":
                name = extract_name_heuristic(text)

            # 3. Upload PDF to Supabase Storage
            safe_filename = file.name.replace(" ", "_")
            storage_path = f"{batch_name}/{uuid.uuid4().hex}_{safe_filename}"
            upload_pdf(pdf_bytes, storage_path)

            # 4. Generate embedding
            embedding = get_embedding(text)

            # 5. Insert into DB
            insert_resume(
                batch_name=batch_name,
                candidate_name=name,
                file_name=file.name,
                storage_path=storage_path,
                extracted_text=text,
                embedding=embedding,
            )

            success_count += 1

        except Exception as e:
            errors.append(f"{file.name}: {e}")

    progress.progress(1.0, text="Done!")

    if success_count:
        st.success(f"✅ {success_count} resume{'s' if success_count != 1 else ''} uploaded to batch **{batch_name}**")

    if errors:
        st.warning(f"{len(errors)} file(s) had issues:")
        for err in errors:
            st.markdown(f"- {err}")
