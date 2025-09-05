from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from django.conf import settings

client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=60)
COLLECTION = settings.QDRANT_COLLECTION


def ensure_collection():
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION not in collections:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
    
ensure_collection()

def upsert_chunks(chunks):
    points = [
        {
            "id": c["id"],
            "vector": c["embedding"],
            "payload": {
                "source": c["source"],
                "title": c["title"],
                "position": c["position"],
                "text_excerpt": c["text_excerpt"],
                "uploaded_at": c.get("uploaded_at"),
                "file_path": c.get("file_path"),
            },
        }
        for c in chunks
    ]
    client.upsert(collection_name=COLLECTION, points=points, wait=True)

def search(query_vector, top_k=5):
    return client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k,
    )
    
def clear_collection(hard=False):
    if hard:
        client.delete_collection(COLLECTION)
        ensure_collection()
    else:
        client.delete(
            collection_name=COLLECTION,
            points_selector=None
        )
        