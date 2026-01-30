"""
Qdrant Hybrid Search Engine
===========================
Step 3: Hybrid search combining dense + sparse vectors with payload filters.
Optimized for low latency (0.1-0.5s).
"""

from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Filter,
    FieldCondition,
    Range,
    MatchValue,
    SearchParams,
    QuantizationSearchParams,
)

from models.schemas import (
    ProductCandidate,
    Product,
    SearchFilters,
    QueryEmbedding,
)


class HybridSearchEngine:
    """
    Performs hybrid search in Qdrant.
    
    Combines:
    - Dense vectors → semantic similarity
    - Sparse vectors → keyword relevance (BM25-style)
    - Payload filters → price, category, availability
    
    Optimizations:
    - Uses gRPC for faster communication
    - Applies quantization for reduced memory
    - Prefetches with oversampling for accuracy
    """
    
    COLLECTION_NAME = "products"
    
    # Hybrid search weights
    DENSE_WEIGHT = 0.7   # Semantic similarity weight
    SPARSE_WEIGHT = 0.3  # Keyword relevance weight
    
    def __init__(self, client: QdrantClient):
        self.client = client
    
    def search(
        self,
        embedding: QueryEmbedding,
        filters: SearchFilters,
        top_k: int = 20,
    ) -> List[ProductCandidate]:
        """
        Perform hybrid search with dense + sparse vectors.
        
        Args:
            embedding: Query embeddings (dense + optional sparse)
            filters: Payload filters to apply
            top_k: Number of results to return (default: 20)
            
        Returns:
            List of ProductCandidate with scores
        """
        # Build Qdrant filter from SearchFilters
        qdrant_filter = self._build_filter(filters)
        
        # Always use dense search (collection uses unnamed vectors)
        # Hybrid search with named vectors requires collection recreation
        results = self._dense_search(
            dense_vector=embedding.dense_vector,
            filter=qdrant_filter,
            top_k=top_k,
        )
        
        # Convert to ProductCandidate objects
        candidates = []
        for result in results:
            product = self._payload_to_product(result.id, result.payload)
            
            candidate = ProductCandidate(
                product=product,
                semantic_score=result.score,
                sparse_score=0.0,  # Will be set in hybrid search
                combined_score=result.score,
            )
            candidates.append(candidate)
        
        return candidates
    
    def _hybrid_search(
        self,
        dense_vector: List[float],
        sparse_vector: Dict[str, float],
        filter: Optional[Filter],
        top_k: int,
    ) -> List[models.ScoredPoint]:
        """
        Execute hybrid search with RRF (Reciprocal Rank Fusion).
        
        Uses Qdrant's query API for efficient hybrid search.
        """
        # Convert sparse vector format
        sparse_indices = [int(k) for k in sparse_vector.keys()]
        sparse_values = list(sparse_vector.values())
        
        # Use prefetch for hybrid search
        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            prefetch=[
                # Dense vector prefetch
                models.Prefetch(
                    query=dense_vector,
                    using="dense",
                    limit=top_k * 2,  # Oversample for better fusion
                    filter=filter,
                ),
                # Sparse vector prefetch
                models.Prefetch(
                    query=models.SparseVector(
                        indices=sparse_indices,
                        values=sparse_values,
                    ),
                    using="sparse",
                    limit=top_k * 2,
                    filter=filter,
                ),
            ],
            query=models.FusionQuery(
                fusion=models.Fusion.RRF,  # Reciprocal Rank Fusion
            ),
            limit=top_k,
        )
        
        return results.points
    
    def _dense_search(
        self,
        dense_vector: List[float],
        filter: Optional[Filter],
        top_k: int,
    ) -> List[models.ScoredPoint]:
        """Execute dense-only vector search"""
        
        # Use unnamed vector (collection uses default vector config)
        # Use query_points instead of search for newer Qdrant API
        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=dense_vector,
            query_filter=filter,
            limit=top_k,
            search_params=SearchParams(
                hnsw_ef=128,
                exact=False,
            ),
        )
        
        return results.points
    
    def _build_filter(self, filters: SearchFilters) -> Optional[Filter]:
        """Convert SearchFilters to Qdrant Filter"""
        must_conditions = []
        must_not_conditions = []
        
        # Price range filter (nested in attributes.price)
        if filters.max_price is not None:
            must_conditions.append(
                FieldCondition(
                    key="attributes.price",
                    range=Range(lte=filters.max_price),
                )
            )
        
        if filters.min_price is not None:
            must_conditions.append(
                FieldCondition(
                    key="attributes.price",
                    range=Range(gte=filters.min_price),
                )
            )
        
        # Category filter - support multiple categories with OR
        if filters.categories:
            if len(filters.categories) == 1:
                must_conditions.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=filters.categories[0].lower()),
                    )
                )
            else:
                # Multiple categories - use should (OR)
                should_conditions = []
                for cat in filters.categories:
                    should_conditions.append(
                        FieldCondition(
                            key="category",
                            match=MatchValue(value=cat.lower()),
                        )
                    )
                must_conditions.append(
                    Filter(should=should_conditions)
                )
        
        # Eco-certified filter (nested in attributes)
        if filters.eco_certified:
            must_conditions.append(
                FieldCondition(
                    key="attributes.eco_certified",
                    match=MatchValue(value=True),
                )
            )
        
        # In-stock filter (nested in attributes.availability)
        if filters.in_stock:
            must_conditions.append(
                FieldCondition(
                    key="attributes.availability.in_stock",
                    match=MatchValue(value=True),
                )
            )
        
        # Excluded brands (nested in attributes)
        for brand in filters.excluded_brands:
            must_not_conditions.append(
                FieldCondition(
                    key="attributes.brand",
                    match=MatchValue(value=brand.lower()),
                )
            )
        
        # Build final filter
        if not must_conditions and not must_not_conditions:
            return None
        
        return Filter(
            must=must_conditions if must_conditions else None,
            must_not=must_not_conditions if must_not_conditions else None,
        )
    
    def _payload_to_product(self, id: str, payload: Dict[str, Any]) -> Product:
        """Convert Qdrant payload to Product object"""
        # Extract from nested structure
        semantic_text = payload.get("semantic_text", {})
        attributes = payload.get("attributes", {})
        availability = attributes.get("availability", {})
        
        # Safely get numeric values (handle None)
        price = attributes.get("price")
        rating = attributes.get("rating")
        reviews_count = attributes.get("reviews_count")
        
        return Product(
            id=payload.get("product_id", str(id)),
            name=semantic_text.get("title", ""),
            price=float(price) if price is not None else 0.0,
            category=payload.get("category", ""),
            description=semantic_text.get("description", ""),
            store=payload.get("store", "Amazon"),
            brand=attributes.get("brand"),
            rating=float(rating) if rating is not None else 0.0,
            reviews_count=int(reviews_count) if reviews_count is not None else 0,
            eco_certified=bool(attributes.get("eco_certified", False)),
            in_stock=bool(availability.get("in_stock", True)),
            specs=attributes.get("specs", {}),
            image_url=payload.get("image_url", "/images/laptop.png"),
        )
    
    def search_similar(
        self,
        product_id: str,
        top_k: int = 10,
        exclude_self: bool = True,
    ) -> List[ProductCandidate]:
        """
        Find similar products to a given product ID.
        Useful for "similar items" recommendations.
        """
        # Get the product's vector
        points = self.client.retrieve(
            collection_name=self.COLLECTION_NAME,
            ids=[product_id],
            with_vectors=True,
        )
        
        if not points:
            return []
        
        point = points[0]
        dense_vector = point.vector.get("dense", [])
        
        # Search for similar products
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=("dense", dense_vector),
            limit=top_k + (1 if exclude_self else 0),
        )
        
        # Convert to candidates, optionally excluding the query product
        candidates = []
        for result in results:
            if exclude_self and str(result.id) == product_id:
                continue
            
            product = self._payload_to_product(result.id, result.payload)
            candidates.append(ProductCandidate(
                product=product,
                semantic_score=result.score,
                combined_score=result.score,
            ))
        
        return candidates[:top_k]
