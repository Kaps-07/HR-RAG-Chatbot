# HR Assistant RAG Chatbot

A production-ready HR Assistant chatbot built with **Retrieval-Augmented Generation (RAG)** using FastAPI, LangChain, ChromaDB, and Azure OpenAI.

---

## 📌 Overview

This chatbot allows employees to ask HR-related questions and get accurate, context-aware answers based on uploaded HR policy documents. It uses RAG to retrieve the most relevant document chunks and passes them to an Azure OpenAI GPT model to generate responses.

---

## 🚀 Features

- Upload and delete HR policy documents (TXT)
- Auto-indexes existing documents on startup
- Semantic search using ChromaDB with cosine similarity
- Multi-turn conversation with chat history
- Source documents shown with cosine similarity scores
- Stateless API — chat history managed on the frontend
- Modular codebase — one responsibility per file

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| LLM | Azure OpenAI (AzureChatOpenAI) |
| Embeddings | Azure OpenAI (AzureOpenAIEmbeddings) |
| Vector Store | ChromaDB (cosine similarity) |
| RAG Pipeline | LangChain LCEL |
| Chunking | RecursiveCharacterTextSplitter |
| Templating | Jinja2 |
| Server | Uvicorn |

---

## 📦 Requirements

- Python 3.10+
- Azure OpenAI resource with GPT and Embedding model deployments

---

## ⚙️ Installation

```bash
git clone https://github.com/your-org/hr-assistant-rag.git
cd hr-assistant-rag
python -m venv venv
venv\Scripts\activate        # On Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

---

## 🔧 Configuration

Create a `.env` file in the project root:

```ini
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
AZURE_OPENAI_GPT_DEPLOYMENT=gpt-4o
INDEX_STORE=vector_db
UPLOAD_FOLDER=data
```

| Variable | Description |
|---|---|
| `AZURE_OPENAI_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_API_VERSION` | API version (e.g. `2024-12-01-preview`) |
| `AZURE_OPENAI_EMBEDDING_MODEL` | Embedding model deployment name |
| `AZURE_OPENAI_GPT_DEPLOYMENT` | GPT model deployment name |
| `INDEX_STORE` | Directory for ChromaDB persistence (default: `vector_db/`) |
| `UPLOAD_FOLDER` | Directory for uploaded TXT files (default: `data/`) |

---

## ▶️ Running the App

```bash
python main.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

**For production:**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🗂️ Project Structure

```
├── main.py                  # FastAPI app, routes, startup indexing
├── config.py                # Centralized environment variable loading
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (never commit this)
├── data/                    # Uploaded TXT files
├── vector_db/               # ChromaDB persistent vector store
├── rag/
│    ├── __init__.py
│    ├── embeddings.py       # AzureOpenAIEmbeddings setup
│    ├── llm.py              # AzureChatOpenAI setup
│    ├── chunking.py         # RecursiveCharacterTextSplitter
│    ├── prompts.py          # ChatPromptTemplate + system prompt
│    ├── vectorstore.py      # Chroma vectorstore + add/delete helpers
│    └── pipeline.py         # RAG search with chat history (LCEL)
└── templates/
     ├── index.html          # Chat UI
     └── manage.html         # Upload/Delete UI
```

---

## 🔍 How It Works

```
User Query
    │
    ▼
AzureOpenAIEmbeddings  ──►  ChromaDB (cosine similarity search)
                                    │
                                    ▼
                            Top-K relevant chunks + scores
                                    │
                                    ▼
                    ChatPromptTemplate (system prompt + chat history + context)
                                    │
                                    ▼
                            AzureChatOpenAI (GPT)
                                    │
                                    ▼
                            Answer + Source Documents
```

1. **Upload** — TXT file is chunked using `RecursiveCharacterTextSplitter` (500 chars, 50 overlap)
2. **Embed** — Each chunk is embedded using `AzureOpenAIEmbeddings`
3. **Store** — Chunks + metadata (`filename`) stored in ChromaDB with cosine similarity
4. **Query** — User question embedded and top-k most similar chunks retrieved
5. **Generate** — Retrieved context + last 5 chat turns passed to GPT via LangChain LCEL
6. **Respond** — Answer + source documents with cosine similarity scores returned to UI

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Chat UI |
| GET | `/manage` | Upload/Delete UI |
| GET | `/list_files` | List uploaded TXT files |
| POST | `/upload` | Upload one or more TXT files |
| POST | `/delete_file` | Delete a file and remove from index |
| POST | `/search` | RAG search — returns answer + sources |

### POST `/search` — Request Body

```json
{
    "query": "What is the leave policy?",
    "top_k": 3,
    "history": [
        {"user": "previous question", "bot": "previous answer"}
    ]
}
```

### POST `/search` — Response

```json
{
    "answer": "Employees are entitled to...",
    "results": [
        {
            "content": "chunk text...",
            "meta": {"filename": "leave_policy.txt"},
            "score": 0.91
        }
    ],
    "history": [
        {"user": "What is the leave policy?", "bot": "Employees are entitled to..."}
    ]
}
```

---

## 📊 Similarity Scores

ChromaDB uses **cosine similarity** (`hnsw:space: cosine`). Scores are converted to similarity (higher = better):

| Score | Meaning |
|---|---|
| 0.9 – 1.0 | Very high relevance |
| 0.7 – 0.9 | Good relevance |
| 0.5 – 0.7 | Moderate relevance |
| < 0.5 | Low relevance |

---

## 🔐 Security

- **Never commit `.env`** — add it to `.gitignore`
- Use **Azure Managed Identity** instead of API keys in production
- Run behind a production ASGI server — never use `reload=True` in production
- Set max upload file size in FastAPI for production use

---

## 🧩 Extending

- Support PDF/DOCX by adding text extraction (`pypdf`, `python-docx`)
- Add per-user document isolation with login/registration
- Add streaming responses using FastAPI `StreamingResponse`
- Deploy to Azure Web App, AWS, GCP, or any Python-compatible host
- Swap ChromaDB for Qdrant or Weaviate for larger scale

---

## 🙏 Credits

- [LangChain](https://www.langchain.com/)
- [ChromaDB](https://www.trychroma.com/)
- [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Bootstrap](https://getbootstrap.com/)

---

*This project is intended for educational and prototyping purposes. For enterprise use, review security and scaling requirements carefully.*
