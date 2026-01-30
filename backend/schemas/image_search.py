"""
Pydantic models for image-based product search
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ImageSearchRequest(BaseModel):
    """Request for image-based product search"""
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    image_url: Optional[str] = Field(None, description="URL to image")
    text_query: Optional[str] = Field(None, description="Optional text query for hybrid search")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum results to return")
    min_similarity: float = Field(default=0.5, ge=0, le=1, description="Minimum similarity score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/product.jpg",
                "text_query": "similar laptops",
                "max_results": 10,
                "min_similarity": 0.6
            }
        }


class ImageEmbedding(BaseModel):
    """Image embedding result"""
    embedding: List[float] = Field(..., description="Image embedding vector")
    dimensions: int = Field(..., description="Embedding dimensions")
    model: str = Field(..., description="Model used for embedding")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class VisualMatch(BaseModel):
    """Visual similarity match result"""
    product_id: str = Field(..., description="Matched product ID")
    product_name: str = Field(..., description="Product name")
    similarity_score: float = Field(..., ge=0, le=1, description="Visual similarity score (0-1)")
    price: Optional[float] = Field(None, description="Product price")
    category: Optional[str] = Field(None, description="Product category")
    brand: Optional[str] = Field(None, description="Product brand")
    image_url: Optional[str] = Field(None, description="Product image URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ImageSearchResponse(BaseModel):
    """Response for image search"""
    matches: List[VisualMatch] = Field(default_factory=list, description="Visual matches")
    total_matches: int = Field(..., description="Total number of matches found")
    query_embedding_dims: int = Field(..., description="Query embedding dimensions")
    search_time_ms: float = Field(..., description="Search time in milliseconds")
    model_used: str = Field(..., description="Model used for search")
    
    class Config:
        json_schema_extra = {
            "example": {
                "matches": [
                    {
                        "product_id": "laptop_001",
                        "product_name": "Dell XPS 13",
                        "similarity_score": 0.92,
                        "price": 799.99,
                        "category": "Laptop",
                        "brand": "Dell"
                    }
                ],
                "total_matches": 5,
                "query_embedding_dims": 512,
                "search_time_ms": 45.2,
                "model_used": "clip-vit-base-patch32"
            }
        }


class MultiModalSearchRequest(BaseModel):
    """Multi-modal search combining image and text"""
    image_data: Optional[str] = Field(None, description="Base64 encoded image")
    image_url: Optional[str] = Field(None, description="Image URL")
    text_query: str = Field(..., description="Text query")
    image_weight: float = Field(default=0.5, ge=0, le=1, description="Weight for image similarity (0-1)")
    text_weight: float = Field(default=0.5, ge=0, le=1, description="Weight for text similarity (0-1)")
    max_results: int = Field(default=10, ge=1, le=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/laptop.jpg",
                "text_query": "gaming laptop under $1000",
                "image_weight": 0.6,
                "text_weight": 0.4,
                "max_results": 10
            }
        }
