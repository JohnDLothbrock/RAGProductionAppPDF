# AI PDF Assistant

An AI-powered Retrieval-Augmented Generation (RAG) application that allows users to upload PDF documents and ask questions about their content using OpenAI embeddings and vector search.

Built with FastAPI, Streamlit, Qdrant, Inngest, and OpenAI.

---

## Features

- Upload PDF documents
- Automatic document chunking
- OpenAI embeddings generation
- Vector storage using Qdrant
- Semantic similarity search
- AI-powered question answering
- Streamlit chat interface
- English / Spanish support
- Async event workflows with Inngest
- Source citation display

---

## Architecture

User uploads PDF → PDF gets chunked → embeddings are generated → vectors stored in Qdrant → user asks a question → semantic search retrieves relevant chunks → OpenAI generates answer using retrieved context.

---

## Tech Stack

- Python
- FastAPI
- Streamlit
- OpenAI API
- Qdrant Vector Database
- Inngest
- AsyncIO
- Requests
- dotenv

---

## Screenshots

### Main Interface

![Home](screenshots/home.png)

---

### Upload PDF

![Upload](screenshots/upload.png)

---

### AI Answer

![Answer](screenshots/answer.png)

---

## 📂 Project Structure

```bash
.
├── main.py
├── streamlit_app.py
├── vector_db.py
├── data_loader.py
├── custom_types.py
├── uploads/
├── screenshots/
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Clone repository

```bash
git clone YOUR_GITHUB_URL
cd YOUR_PROJECT_NAME
```

---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Configure environment variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key
INNGEST_API_BASE=http://127.0.0.1:8288/v1
```

---

### 4. Start Qdrant

Using Docker:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

---

### 5. Start FastAPI backend

```bash
uvicorn main:app --reload
```

---

### 6. Start Inngest dev server

```bash
npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery
```

---

### 7. Start Streamlit frontend

```bash
streamlit run streamlit_app.py
```

---

## - How It Works

### PDF Ingestion Pipeline

1. User uploads PDF
2. PDF text is extracted
3. Text is split into chunks
4. OpenAI embeddings are generated
5. Embeddings stored in Qdrant

### Query Pipeline

1. User asks question
2. Question embedding generated
3. Similar chunks retrieved from Qdrant
4. Retrieved context sent to OpenAI
5. AI generates contextual answer

---

## - Future Improvements

- Authentication system
- User accounts
- Multi-document sessions
- Chat memory persistence
- Docker deployment
- Streaming AI responses
- Citation highlighting
- Cloud deployment

---
## 👨‍💻 Author

Juan Andrey Ureña Chaves

Computer Software Engineering project:
- Backend Development
- AI Applications
- Data Engineering
- FastAPI & Python
