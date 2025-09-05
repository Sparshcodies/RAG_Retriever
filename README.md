# RAG Demo App

A minimal Retrieval-Augmented Generation (RAG) system built with **Django + Qdrant + Gemini + Cohere**.  
This app lets users upload documents (PDF/DOCX) or paste text, indexes them into Qdrant with embeddings, and provides a chat-like interface to query across documents with reranking and grounding verification.

---

## 🚀 Live Demo

Hosted at: [https://&lt;your-pythonanywhere-username&gt;.pythonanywhere.com](https://&lt;your-pythonanywhere-username&gt;.pythonanywhere.com)

- First screen loads without console errors.  
- You can upload files, ask questions, and see retrieved chunks, reranked results, and grounded answers with citations.

---

## 🏗️ Architecture

![Architecture Diagram](docs/architecture.png)

**Flow:**

1. Upload Text/File → Extract text → Chunk into 800 tokens with 80 overlap.
2. Embeddings → Generated using Google Gemini (768-dim vectors).  
3. Vector DB → Stored in Qdrant with COSINE similarity.  
4. Retriever → Top-10 chunks retrieved.  
5. Reranker → Cohere Rerank API trims to top-3.  
6. LLM Answer → Gemini generates grounded response.  
7. Verification → Grounding check to reject hallucinations.  
8. UI → Tailwind + minimal JS.

---

## ⚙️ Configuration

- **Chunk size**: 800 tokens  
- **Chunk overlap**: 80 tokens  
- **Retriever**: Qdrant, top_k = 10  
- **Reranker**: Cohere, top_k = 3  
- **LLM provider**: Gemini (for embeddings + generation)  
- **Vector dimensions**: 768  
- **Distance metric**: Cosine  

---

## 📦 Setup

### 1. Clone the repo

```bash
git clone https://github.com/&lt;your-username&gt;/&lt;your-repo&gt;.git
cd &lt;your-repo&gt;
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment variables

Copy `.env.example` to `.env` and set your keys:

```env
QDRANT_URL=...
QDRANT_API_KEY=...
QDRANT_COLLECTION=rag_demo
GEMINI_API_KEY=...
COHERE_API_KEY=...
DJANGO_SECRET_KEY=...
```

### 4. Run locally

```bash
python manage.py runserver
```

Visit [http://localhost:8000](http://localhost:8000).

### 5. Deploy (PythonAnywhere example)

- Upload repo to PythonAnywhere.
- Set env vars under **Web &gt; WSGI config**.
- Run migrations & reload app.

---

## 📊 Evaluation

Minimal gold set (5 Q/A pairs tested):

| Query                                  | Expected             | Got                  | Correct? |
| -------------------------------------- | -------------------- | -------------------- | -------- |
| What is the candidate’s notice period? | 2 months             | 2 months             | ✅        |
| When does the offer letter start?      | 1st Sept 2025        | 1st Sept 2025        | ✅        |
| Who signed the document?               | HR Manager           | HR Manager           | ✅        |
| What is the role offered?              | Software Engineer    | Software Engineer    | ✅        |
| What is the offered CTC?               | ₹10,00,000 per annum | ₹10,00,000 per annum | ✅        |

**Precision:** ~100% (5/5)  
**Recall:** Within top-10 retrievals for all queries.

---

## 📝 Remarks

- **Limits:** Free tiers of Cohere & Gemini were used, may throttle under heavy load.
- **Trade-offs:**
- Used simple fixed-size chunking instead of semantic chunking for speed.
- Cohere reranker adds latency but boosts precision.
- **Next steps:**
- Add caching layer to reduce embedding calls.
- Support images & tables from PDFs.
- Better eval metrics with a larger gold set.

---

## 📄 Submission Checklist

- ✅ Live URL (PythonAnywhere)
- ✅ Public GitHub repo
- ✅ README (setup, architecture diagram, resume link)
- ✅ Index config (Qdrant, 768-dim, cosine)
- ✅ Remarks section

---

## 📎 Links

- **Live Demo**: [Python Demo Link](sparshsahu.pythonanywhere.com)
- **GitHub Repo**: [Repo Link](https://github.com/Sparshcodies/RAG_Retriever.git)
- **Resume**: [Google Drive Link](https://drive.google.com/file/d/1mPGwlS4fyLZ_zW5LePxdP9hEo3SaRsYc/view?usp=sharing)
