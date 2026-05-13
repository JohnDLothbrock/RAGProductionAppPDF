import asyncio
from pathlib import Path
import os
import datetime

import streamlit as st
import inngest
import requests
from dotenv import load_dotenv

load_dotenv()

# SESSION STATE
if "messages" not in st.session_state:
    st.session_state.messages = []

# PAGE CONFIG
st.set_page_config(
    page_title="AI PDF Assistant",
    page_icon="📄",
    layout="centered"
)

# LANGUAGE SELECTOR
language = st.selectbox(
    "🌐 Language",
    ["English", "Español"]
)

# TRANSLATIONS
TEXTS = {

    "English": {
        "sidebar_title": "⚙️ AI PDF Assistant",
        "built_with": "Built with:",
        "info": "Upload PDFs and ask questions!",
        "upload_title": "📤 Upload PDF",
        "upload_label": "Choose a PDF",
        "upload_spinner": "Uploading and processing PDF...",
        "upload_success": "PDF ingested successfully:",
        "question_title": "## 💬 Ask Questions About Your Documents",
        "question_label": "Your question",
        "ask_button": "Ask AI",
        "answer_spinner": "Generating answer...",
        "sources": "📚 View Sources",
        "no_answer": "(No answer)"
    },

    "Español": {
        "sidebar_title": "⚙️ Asistente IA PDF",
        "built_with": "Construido con:",
        "info": "¡Sube PDFs y haz preguntas!",
        "upload_title": "📤 Subir PDF",
        "upload_label": "Selecciona un PDF",
        "upload_spinner": "Subiendo y procesando PDF...",
        "upload_success": "PDF procesado correctamente:",
        "question_title": "## 💬 Haz Preguntas Sobre Tus Documentos",
        "question_label": "Tu pregunta",
        "ask_button": "Preguntar a la IA",
        "answer_spinner": "Generando respuesta...",
        "sources": "📚 Ver Fuentes",
        "no_answer": "(Sin respuesta)"
    }
}

# CURRENT LANGUAGE
t = TEXTS[language]

# CSS
st.markdown("""
<style>

/* Hide Streamlit menu */
#MainMenu {
    visibility: hidden;
}

/* Keep header visible so sidebar toggle works */
header {
    background: transparent;
}

/* Hide only Streamlit branding/menu */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* Hide footer */
footer {
    visibility: hidden;
}

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
    background-color: #161B22;
    color: white;
    border: 1px solid #30363D;
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

# SIDEBAR
with st.sidebar:

    st.title(t["sidebar_title"])

    st.write(t["built_with"])

    st.markdown("""
    - FastAPI
    - OpenAI
    - Qdrant
    - Inngest
    - Streamlit
    """)

    st.divider()

    if st.button("🗑 Clear Chat"):

        st.session_state.messages = []

        st.rerun()

    st.info(t["info"])

# HEADER
st.markdown(
    f"""
    <h1 style='text-align: center;'>
        📄 AI PDF Assistant
    </h1>

    <p style='text-align: center; color: gray;'>
        {t["info"]}
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()

# INNGEST CLIENT
@st.cache_resource
def get_inngest_client() -> inngest.Inngest:

    return inngest.Inngest(
        app_id="rag_app",
        is_production=False
    )

# SAVE PDF
def save_uploaded_pdf(file) -> Path:

    uploads_dir = Path("uploads")

    uploads_dir.mkdir(
        parents=True,
        exist_ok=True
    )

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

# PDF UPLOAD SECTION
with st.container():

    st.subheader(t["upload_title"])

    uploaded = st.file_uploader(
        t["upload_label"],
        type=["pdf"],
        accept_multiple_files=False
    )

    if uploaded is not None:

        with st.spinner(t["upload_spinner"]):

            path = save_uploaded_pdf(uploaded)

            asyncio.run(
                send_rag_ingest_event(path)
            )

        st.success(
            f"{t['upload_success']} {path.name}"
        )

# QUERY SECTION
st.divider()

st.markdown(
    t["question_title"]
)

# SEND QUERY EVENT
async def send_rag_query_event(
    question: str,
    top_k: int
):

    client = get_inngest_client()

    result = await client.send(
        inngest.Event(
            name="rag/query_pdf_ai",
            data={
                "question": question,
                "top_k": top_k,
                "language": language
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

    start = datetime.datetime.now().timestamp()

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

            if status in (
                "Failed",
                "Cancelled"
            ):

                raise RuntimeError(
                    f"Function run {status}"
                )

        current_time = datetime.datetime.now().timestamp()

        if current_time - start > timeout_s:

            raise TimeoutError(
                f"Timed out waiting for run output "
                f"(last status: {last_status})"
            )

# QUESTION FORM
with st.form("rag_query_form"):

    question = st.text_input(
        t["question_label"]
    )

    submitted = st.form_submit_button(
        t["ask_button"]
    )

    if submitted and question.strip():

        with st.spinner(
            t["answer_spinner"]
        ):

            event_id = asyncio.run(
                send_rag_query_event(
                    question.strip(),
                    5
                )
            )

            output = wait_for_run_output(
                event_id
            )

            answer = output.get(
                "answer",
                ""
            )

            sources = output.get(
                "sources",
                []
            )

        # SAVE USER MESSAGE
        st.session_state.messages.append({
            "role": "user",
            "content": question,
            "time": datetime.datetime.now().strftime("%H:%M")
        })

        # SAVE AI MESSAGE
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer or t["no_answer"],
            "time": datetime.datetime.now().strftime("%H:%M")
        })

# DISPLAY CHAT HISTORY
for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])

        st.caption(msg["time"])

# SOURCES
if len(st.session_state.messages) > 0:

    last_sources = sources if "sources" in locals() else []

    if last_sources:

        with st.expander(
            t["sources"]
        ):

            for i, s in enumerate(last_sources, start=1):

                st.info(f"Source {i}: {s}")