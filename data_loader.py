#here, I will use llama index to load the PDF and embed them

from openai import OpenAI
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

#we cannot embed the entire pdf
#remember: embed means basically just convert the data into a vector to store it in the db
#for the pdf file we need to chunk it to smaller pieces and then embed those pieces
EMBED_MODEL = "text-embedding-3-large"
EMBED_DIM = 3072

splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)

#next function basically does this: PDF → extract text → split into smaller chunks → return chunks
#This is necessary because LLMs and embedding models do NOT work well with huge documents at once
def load_and_chunk_pdf(pdf_path: str):
    docs = PDFReader().load_data(file=pdf_path)
    texts = [d.text for d in docs if getattr(d, "text", None)]
    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))
    return chunks

#this one receives chunks of text, sends them to an embedding model(openAi), converts text into vectors, returns embeddings
def embed_texts(texts: list[str]) ->list[list[float]]:
    response = client.embeddings.create(
        model= EMBED_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]

