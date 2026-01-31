import os
import hashlib
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    PointStruct,
    Filter,
    FieldCondition,
    Range,
    MatchValue,
)


class QdrantManager:
    """
    Manages Qdrant connection and collection operations.
    
    Qdrant runs locally via Docker:
    docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
    """
    
    COLLECTION_NAME = "products"
    DENSE_VECTOR_SIZE = 384  # sentence-transformers/all-MiniLM-L6-v2
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        grpc_port: int = None,
    ):
        """
        Initialize Qdrant connection.
        
        Args:
            host: Qdrant host (default: localhost)
            port: REST API port (default: 6333)
            grpc_port: gRPC port for faster ops (default: 6334)
        """
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        self.grpc_port = grpc_port or int(os.getenv("QDRANT_GRPC_PORT", "6334"))
        
        self._client: Optional[QdrantClient] = None
    
    @property
    def client(self) -> QdrantClient:
        """Lazy initialization of Qdrant client"""
        if self._client is None:
            self._client = QdrantClient(
                host=self.host,
                port=self.port,
                grpc_port=self.grpc_port,
                prefer_grpc=True,  # Use gRPC for better performance
            )
        return self._client
    
    def health_check(self) -> bool:
        """Check if Qdrant is running and accessible"""
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False
    
    def create_collection(self, recreate: bool = False) -> bool:
        """
        Create the products collection with hybrid vectors.
        
        Schema:
        - dense_vector: 384-dim semantic embedding
        - sparse_vector: BM25-style keyword relevance
        - payload: product metadata for filtering
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == self.COLLECTION_NAME for c in collections)
            
            if exists and not recreate:
                return True
            
            if exists and recreate:
                self.client.delete_collection(self.COLLECTION_NAME)
            
            # Create collection with hybrid vectors
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config={
                    "dense": VectorParams(
                        size=self.DENSE_VECTOR_SIZE,
                        distance=Distance.COSINE,
                    )
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams(
                        index=SparseIndexParams(
                            on_disk=False,
                        )
                    )
                },
            )
            
            # Create payload indexes for fast filtering
            self._create_payload_indexes()
            
            return True
            
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    def _create_payload_indexes(self):
        """Create indexes on frequently filtered fields"""
        
        # Price index for range queries
        self.client.create_payload_index(
            collection_name=self.COLLECTION_NAME,
            field_name="price",
            field_schema=models.PayloadSchemaType.FLOAT,
        )
        
        # Category index for exact match
        self.client.create_payload_index(
            collection_name=self.COLLECTION_NAME,
            field_name="category",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        
        # Brand index
        self.client.create_payload_index(
            collection_name=self.COLLECTION_NAME,
            field_name="brand",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        
        # Eco certification index
        self.client.create_payload_index(
            collection_name=self.COLLECTION_NAME,
            field_name="eco_certified",
            field_schema=models.PayloadSchemaType.BOOL,
        )
        
        # Stock availability index
        self.client.create_payload_index(
            collection_name=self.COLLECTION_NAME,
            field_name="in_stock",
            field_schema=models.PayloadSchemaType.BOOL,
        )
    
    def upsert_products(
        self,
        products: List[Dict[str, Any]],
        dense_vectors: List[List[float]],
        sparse_vectors: Optional[List[Dict[int, float]]] = None,
    ) -> bool:
        """
        Upsert products into Qdrant.
        
        Args:
            products: List of product dictionaries
            dense_vectors: Dense embeddings for each product
            sparse_vectors: Optional sparse vectors (BM25)
        """
        try:
            points = []
            
            for i, (product, dense_vec) in enumerate(zip(products, dense_vectors)):
                # Build vectors dict
                vectors = {"dense": dense_vec}
                
                if sparse_vectors and i < len(sparse_vectors):
                    sparse = sparse_vectors[i]
                    vectors["sparse"] = models.SparseVector(
                        indices=list(sparse.keys()),
                        values=list(sparse.values()),
                    )
                
                # Build payload (product metadata)
                payload = {
                    "product_id": product.get("id", str(i)),  # Store original ID in payload
                    "name": product.get("name", ""),
                    "price": float(product.get("price", 0)),
                    "category": product.get("category", "").lower(),
                    "description": product.get("description", ""),
                    "store": product.get("store", ""),
                    "brand": product.get("brand", "").lower() if product.get("brand") else "",
                    "rating": float(product.get("rating", 0)),
                    "reviews_count": int(product.get("reviews_count", 0)),
                    "eco_certified": bool(product.get("eco_certified", False)),
                    "in_stock": bool(product.get("in_stock", True)),
                    "specs": product.get("specs", {}),
                    "image_url": product.get("image_url", ""),
                }
                
                # Convert string ID to integer hash for Qdrant
                product_id = product.get("id", str(i))
                id_hash = int(hashlib.md5(product_id.encode()).hexdigest()[:16], 16)
                
                points.append(PointStruct(
                    id=id_hash,
                    vector=vectors,
                    payload=payload,
                ))
            
            # Batch upsert for efficiency
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=points,
            )
            
            return True
            
        except Exception as e:
            print(f"Error upserting products: {e}")
            return False
    
    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.COLLECTION_NAME)
            return {
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status,
            }
        except Exception:
            return None
    
    def delete_products(self, product_ids: List[str]) -> bool:
        """Delete products by IDs"""
        try:
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=models.PointIdsList(points=product_ids),
            )
            return True
        except Exception:
            return False
    
    def close(self):
        """Close the Qdrant connection"""
        if self._client:
            self._client.close()
            self._client = None
