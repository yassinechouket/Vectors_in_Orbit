"""
Minimal test backend to verify Qdrant connectivity
This will help isolate whether the issue is Qdrant or the recommendation pipeline
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from services.qdrant.client import QdrantManager

app = FastAPI(title="Minimal Test API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "Minimal test API is running"}

@app.get("/health")
def health():
    """Simple health check"""
    try:
        qm = QdrantManager()
        qdrant_ok = qm.health_check()
        info = qm.get_collection_info() if qdrant_ok else None
        
        return {
            "status": "healthy",
            "qdrant_connected": qdrant_ok,
            "products_count": info['points_count'] if info else 0
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/test-search")
def test_search(query: str = "laptop"):
    """Minimal search test"""
    try:
        from sentence_transformers import SentenceTransformer
        from services.qdrant.hybrid_search import HybridSearchEngine
        
        # Create embedding
        model = SentenceTransformer("all-MiniLM-L6-v2")
        vector = model.encode(query).tolist()
        
        # Search Qdrant
        qm = QdrantManager()
        search_engine = HybridSearchEngine(qm)
        
        results = search_engine.search(
            query_vector=vector,
            limit=5
        )
        
        return {
            "query": query,
            "results_count": len(results),
            "results": [
                {
                    "id": r.product.id,
                    "name": r.product.name,
                    "price": r.product.price,
                    "score": r.semantic_score
                }
                for r in results[:3]
            ]
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    print("Starting minimal test server...")
    print("This will help diagnose if Qdrant is working properly")
    print("Access at: http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
