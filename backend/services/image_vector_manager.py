"""
Qdrant Integration for Image Vectors

This module handles storing and searching image embeddings in Qdrant.
Creates a separate collection for image vectors parallel to the text collection.
"""
from typing import List, Dict, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)


class ImageVectorManager:
    """Manages image vectors in Qdrant"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "products_image_vectors"
    ):
        """
        Initialize image vector manager
        
        Args:
            host: Qdrant host
            port: Qdrant port
            collection_name: Name of image vector collection
        """
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.vector_size = 512  # CLIP embedding size
    
    def create_collection(self, recreate: bool = False) -> bool:
        """
        Create Qdrant collection for image vectors
        
        Args:
            recreate: If True, delete existing collection first
            
        Returns:
            True if successful
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if exists and recreate:
                self.client.delete_collection(self.collection_name)
                print(f"Deleted existing collection: {self.collection_name}")
            
            if not exists or recreate:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created collection: {self.collection_name}")
            
            return True
            
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    def upsert_image_vector(
        self,
        product_id: str,
        image_embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Store or update image embedding for a product
        
        Args:
            product_id: Unique product identifier
            image_embedding: CLIP embedding vector
            metadata: Product metadata (name, price, category, etc.)
            
        Returns:
            True if successful
        """
        try:
            point = PointStruct(
                id=product_id,
                vector=image_embedding,
                payload=metadata
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return True
            
        except Exception as e:
            print(f"Error upserting image vector: {e}")
            return False
    
    def batch_upsert_image_vectors(
        self,
        product_data: List[Dict[str, Any]]
    ) -> int:
        """
        Batch insert image vectors
        
        Args:
            product_data: List of dicts with 'id', 'image_embedding', and metadata
            
        Returns:
            Number of vectors inserted
        """
        try:
            points = []
            
            for item in product_data:
                point = PointStruct(
                    id=item['id'],
                    vector=item['image_embedding'],
                    payload={k: v for k, v in item.items() if k not in ['id', 'image_embedding']}
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            return len(points)
            
        except Exception as e:
            print(f"Error batch upserting: {e}")
            return 0
    
    def search_similar_images(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for visually similar products
        
        Args:
            query_embedding: Query image embedding
            limit: Max results
            score_threshold: Minimum similarity score
            filters: Optional filters (category, price range, etc.)
            
        Returns:
            List of similar products with scores
        """
        try:
            # Build filter if provided
            query_filter = None
            if filters:
                conditions = []
                
                if 'category' in filters:
                    conditions.append(
                        FieldCondition(
                            key="category",
                            match=MatchValue(value=filters['category'])
                        )
                    )
                
                if 'min_price' in filters:
                    conditions.append(
                        FieldCondition(
                            key="price",
                            range={"gte": filters['min_price']}
                        )
                    )
                
                if 'max_price' in filters:
                    conditions.append(
                        FieldCondition(
                            key="price",
                            range={"lte": filters['max_price']}
                        )
                    )
                
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # Format results
            matches = []
            for result in results:
                match = {
                    'product_id': result.id,
                    'similarity_score': result.score,
                    **result.payload
                }
                matches.append(match)
            
            return matches
            
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                'name': self.collection_name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'status': info.status,
                'vector_size': self.vector_size
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def health_check(self) -> bool:
        """Check if Qdrant is accessible"""
        try:
            self.client.get_collections()
            return True
        except:
            return False


# Singleton instance
image_vector_manager = ImageVectorManager()
