import os
import time
import docx
import tempfile
from PyPDF2 import PdfReader
from user.services import gemini, qdrant, cohere
from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render
from django.utils.timezone import now
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

TOP_K_RAW = 15
FINAL_N = 5

def extract_text_from_pdf(file_path):
    text = []
    reader = PdfReader(file_path)
    for page in reader.pages:
        text.append(page.extract_text() or "")
    return "\n".join(text)

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def chunk_text(text, source="UserUpload", title=None, size=800, overlap=80, file_path=None):
    words = text.split()
    chunks = []
    pos = 0
    timestamp = now().isoformat()
    for i in range(0, len(words), size - overlap):
        chunk_text = " ".join(words[i:i+size])
        emb = gemini.embed_text(chunk_text)
        chunks.append({
            "id": pos,
            "source": source,
            "title": title or source,
            "position": pos,
            "text_excerpt": chunk_text[:800],
            "embedding": emb,
            "uploaded_at": timestamp,
            "file_path": file_path,
        })
        pos += 1
    return chunks

@api_view(['POST'])
def ingest(request):
    text = request.data.get("text")
    if not text:
        return Response({"error": "No text provided"}, status=400)

    docs_dir = os.path.join(settings.MEDIA_ROOT, "documents")
    os.makedirs(docs_dir, exist_ok=True)
    temp_path = os.path.join(docs_dir, f"userinput_{int(time.time())}.txt")
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(text)

    chunks = []
    words = text.split()
    size, overlap = 800, 80
    pos = 0
    for i in range(0, len(words), size - overlap):
        chunk_text = " ".join(words[i:i+size])
        emb = gemini.embed_text(chunk_text)
        chunks.append({
            "id": pos,
            "source": "UserInput",
            "title": f"UserInput {pos}",
            "position": pos,
            "text_excerpt": chunk_text[:800],
            "embedding": emb,
            "file_path": temp_path,
        })
        pos += 1

    qdrant.upsert_chunks(chunks)
    return Response({"status": "indexed", "chunks": len(chunks), "file_path": temp_path})

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def ingest_file(request):
    file = request.FILES.get("file")
    if not file:
        return Response({"error": "No file uploaded"}, status=400)
    
    docs_dir = os.path.join(settings.MEDIA_ROOT, "documents")
    os.makedirs(docs_dir, exist_ok=True)
    file_path = os.path.join(docs_dir, file.name)

    with open(file_path, "wb") as f:
        for chunk in file.chunks():
            f.write(chunk)

    ext = os.path.splitext(file.name)[1].lower()
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        text = extract_text_from_docx(file_path)
    else:
        os.remove(file_path)
        return Response({"error": "Unsupported file format"}, status=400)

    title = os.path.splitext(file.name)[0]
    chunks = chunk_text(text, source="UserUpload", title=title, file_path=file_path)
    qdrant.upsert_chunks(chunks)

    return Response({"status": "file indexed", "chunks": len(chunks), "file_path": file_path})


@api_view(['POST'])
def query(request):
    query = request.data.get("query")
    if not query:
        return Response({"error": "No query provided"}, status=400)

    start_time = time.time()
    query_emb = gemini.embed_text(query)
    raw_hits = qdrant.search(
        query_vector=query_emb,
        top_k=TOP_K_RAW
    )
    
    candidates = []
    candidate_vecs = []
    for hit in raw_hits:
        payload = hit.payload
        candidates.append({
            "id": hit.id,
            "text_excerpt": payload.get("text_excerpt",""),
            "title": payload.get("title") or payload.get("source"),
            "position": payload.get("position"),
            "file_path": payload.get("file_path")
        })
        candidate_vecs.append(hit.vector if hasattr(hit, "vector") else None)

    final_candidates = []
    reranker_used = "none"
    try:
        docs_texts = [c["text_excerpt"] for c in candidates]
        print("Docs to rerank:", candidates) 
        ranked = cohere.cohere_rerank(query, docs_texts, top_k = FINAL_N) 
        top_indices = [r.index for r in ranked]
        final_candidates = [candidates[i] for i in top_indices]
        reranker_used = "cohere"
    except Exception as e:
        print(f"Error during reranking: {e}")
        
    retrieve_ms = int((time.time() - start_time) * 1000)
    gen_start = time.time()
    answer_text = gemini.generate_grounded_answer(query, final_candidates)
    gen_ms = int((time.time() - gen_start) * 1000)

    verify = gemini.verify_answer_is_grounded(answer_text, final_candidates)
    if not verify.get("supported", False):
        answer_text = "I could not find a reliable answer in the provided sources."
        provenance = {"verified": False, "issues": verify.get("unsupported_sentences", [])}
    else:
        provenance = {"verified": True, "issues": []}

    total_ms = int((time.time() - start_time) * 1000)
    
    citations = []
    for i, s in enumerate(final_candidates, start=1):
        citations.append({
            "id": i,
            "source": s.get("title"),
            "position": s.get("position"),
            "text_excerpt": s.get("text_excerpt"),
            "file_path": s.get("file_path")
        })
        
    return Response({
        "answer": answer_text,
        "citations": citations,
        "timing_ms": {"retrieve_ms": retrieve_ms, "generate_ms": gen_ms, "total_ms": total_ms},
        "reranker_used": reranker_used,
        "verification": provenance
    })
        
    # results = qdrant.search(query_emb, top_k=5)

    # snippets = [
    #     {
    #         "text_excerpt": r.payload.get("text_excerpt", ""),
    #         "source": r.payload.get("source", ""),
    #         "position": r.payload.get("position", -1),
    #     }
    #     for r in results
    # ]

    # answer = gemini.generate_answer(query, snippets)
    # return Response({
    #     "answer": answer,
    #     "citations": snippets,
    # })
    
@api_view(['GET'])
def download_file(request):
    path = request.GET.get("path")
    if not path or not os.path.exists(path):
        return Response({"error": "File not found"}, status=404)
    return FileResponse(open(path, "rb"), as_attachment=True, filename=os.path.basename(path))
    
def chat_ui(request):
    return render(request, "chat.html")