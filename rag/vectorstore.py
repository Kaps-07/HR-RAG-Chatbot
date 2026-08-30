from langchain_chroma import Chroma
from rag.embeddings import embeddings
from rag.chunking import split_text
from config import INDEX_STORE

ALLOWED_EXTENSIONS = {"txt"}

vectorstore = Chroma(
    collection_name="hr_docs",
    embedding_function=embeddings,
    persist_directory=INDEX_STORE,
    collection_metadata={"hnsw:space": "cosine"},
)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def add_file_to_index(filename, content):
    """Chunk and add a document to the vectorstore with metadata."""
    chunks = split_text(content, filename)
    vectorstore.add_documents(chunks)


def delete_file_from_index(filename):
    """Delete all chunks for a given filename from the vectorstore."""
    results = vectorstore.get(where={"filename": filename})
    if results["ids"]:
        vectorstore.delete(ids=results["ids"])


def has_documents():
    return vectorstore._collection.count() > 0
