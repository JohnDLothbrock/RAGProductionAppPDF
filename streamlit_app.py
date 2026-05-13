import asyncio
from pathlib import Path
import time
import os

import streamlit as st
import inngest
import requests
from dotenv import load_dotenv

load_dotenv()

#page Config
st.set_page_config(
    page_title="AI PDF Assistant",
    page_icon="📄",
    layout="centered"
)


#CSS
st.markdown("""
<style>

/* Main background */
.stApp {
    background-color: #0E1117;
    color: white;
}

/* Main container */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Buttons */
.stButton > button {
    background-color: #4F46E5;
    color: white;
    border-radius: 10px;
    border: none;
    height: 3em;
    width: 100%;
    font-size: 16px;
    font-weight: 600;
}

/* Text input */
.stTextInput > div > div > input {
    border-radius: 10px;
}

/* Number input */
.stNumberInput > div > div > input {
    border-radius: 10px;
}

/* File uploader */
.stFileUploader {
    border: 2px dashed #4F46E5;
    padding: 1rem;
    border-radius: 10px;
    background-color: #161B22;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 10px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #161B22;
}

</style>
""", unsafe_allow_html=True)


# sidebar
with st.sidebar:
    st.title("⚙ AI PDF Assistant")
    st.write("Built with:")
    st.markdown("""
    - FastAPI
    - OpenAI
    - Qdrant
    - Inngest
    - Streamlit
    """)
    st.divider()
    st.info("Upload PDFs and ask questions!")


# Inngest client
@st.cache_resource
def get_inngest_client() -> inngest.Inngest:
    return inngest.Inngest(
        app_id="rag_app",
        is_production=False
    )



# SAVE PDF
def save_uploaded_pdf(file) -> Path:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    file_path = uploads_dir / file.name

    file_bytes = file.getbuffer()
    file_path.write_bytes(file_bytes)

    return file_path


# SEND INGEST EVENT
async def send_rag_ingest_event(pdf_path: Path) -> None:
    client = get_inngest_client()

    await client.send(
        inngest.Event(
            name="rag/ingest_pdf",
            data={
                "pdf_path": str(pdf_path.resolve()),
                "source_id": pdf_path.name,
            },
        )
    )


# HEADER
st.markdown("""
# 📄 AI PDF Assistant

Ask questions about your PDFs
""")

st.divider()


# PDF UPLOAD SECTION
with st.container():

    st.subheader("📤 Upload PDF")

    uploaded = st.file_uploader(
        "Choose a PDF",
        type=["pdf"],
        accept_multiple_files=False
    )

    if uploaded is not None:

        with st.spinner("Uploading and processing PDF..."):

            path = save_uploaded_pdf(uploaded)

            asyncio.run(send_rag_ingest_event(path))

            time.sleep(0.3)

        st.success(f"PDF ingested successfully: {path.name}")


# QUERY SECTION
st.divider()

st.markdown("## 💬 Ask Here Questions About Your Documents")


# SEND QUERY EVENT
async def send_rag_query_event(question: str, top_k: int):

    client = get_inngest_client()

    result = await client.send(
        inngest.Event(
            name="rag/query_pdf_ai",
            data={
                "question": question,
                "top_k": top_k,
            },
        )
    )

    return result[0]

# INNGEST API BASE
def _inngest_api_base() -> str:
    return os.getenv(
        "INNGEST_API_BASE",
        "http://127.0.0.1:8288/v1"
    )


# FETCH RUNS
def fetch_runs(event_id: str) -> list[dict]:

    url = f"{_inngest_api_base()}/events/{event_id}/runs"

    resp = requests.get(url)

    resp.raise_for_status()

    data = resp.json()

    return data.get("data", [])


# WAIT FOR OUTPUT
def wait_for_run_output(
    event_id: str,
    timeout_s: float = 120.0,
    poll_interval_s: float = 0.5
) -> dict:

    start = time.time()

    last_status = None

    while True:

        runs = fetch_runs(event_id)

        if runs:

            run = runs[0]

            status = run.get("status")

            last_status = status or last_status

            if status in (
                "Completed",
                "Succeeded",
                "Success",
                "Finished"
            ):
                return run.get("output") or {}

            if status in ("Failed", "Cancelled"):
                raise RuntimeError(f"Function run {status}")

        if time.time() - start > timeout_s:
            raise TimeoutError(
                f"Timed out waiting for run output "
                f"(last status: {last_status})"
            )

        time.sleep(poll_interval_s)


# QUESTION FORM
with st.form("rag_query_form"):

    col1, col2 = st.columns([4, 1])

    with col1:
        question = st.text_input(
            "Your question"
        )

    submitted = st.form_submit_button("Ask AI")

    if submitted and question.strip():

        with st.spinner("Generating answer..."):

            event_id = asyncio.run(
                send_rag_query_event(
                    question.strip(),
                    int(top_k)
                )
            )

            output = wait_for_run_output(event_id)

            answer = output.get("answer", "")

            sources = output.get("sources", [])


        # CHAT UI
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            st.write(answer or "(No answer)")


        # SOURCES
        if sources:

            with st.expander("📚 View Sources"):

                for s in sources:
                    st.code(s)