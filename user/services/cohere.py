import cohere
from django.conf import settings

COHERE_API_KEY = settings.COHERE_API_KEY

def cohere_rerank(query: str, docs: list, top_k: int = 5):
    if not COHERE_API_KEY:
        raise RuntimeError("Cohere key not configured.")
    co = cohere.ClientV2(COHERE_API_KEY)
    
    response = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=docs,
        top_n=top_k
    )
    
    return response.results
