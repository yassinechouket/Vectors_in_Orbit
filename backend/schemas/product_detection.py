"""
Pydantic models for product page detection
"""
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ProductPageDetection(BaseModel):
    """Result of product page detection"""
    is_product_page: bool = Field(..., description="Whether the page is a product page")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    source: str = Field(..., description="Detection source: schema.org, opengraph, pattern_match")
    detection_time: datetime = Field(default_factory=datetime.utcnow)


class ExtractedProductInfo(BaseModel):
    """Structured product information extracted from HTML"""
    name: Optional[str] = Field(None, description="Product name/title")
    category: Optional[str] = Field(None, description="Product category")
    price: Optional[float] = Field(None, ge=0, description="Current price")
    original_price: Optional[float] = Field(None, ge=0, description="Original price (if on sale)")
    currency: Optional[str] = Field(None, description="Currency code (USD, EUR, etc)")
    brand: Optional[str] = Field(None, description="Brand name")
    description: Optional[str] = Field(None, description="Product description")
    images: List[str] = Field(default_factory=list, description="Product image URLs")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Technical specs")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating (0-5)")
    review_count: Optional[int] = Field(None, ge=0, description="Number of reviews")
    availability: Optional[str] = Field(None, description="Stock availability status")
    sku: Optional[str] = Field(None, description="SKU/Product ID")
    url: Optional[str] = Field(None, description="Product page URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Dell XPS 13",
                "category": "Laptop",
                "price": 799.99,
                "currency": "USD",
                "brand": "Dell",
                "rating": 4.7,
                "review_count": 5234,
                "images": ["https://example.com/image1.jpg"],
                "specifications": {
                    "processor": "Intel i5",
                    "ram": "8GB",
                    "storage": "256GB SSD"
                }
            }
        }


class ProductPageRequest(BaseModel):
    """Request to detect and extract product page info"""
    html: str = Field(..., description="HTML content of the page")
    url: str = Field(..., description="URL of the page")


class ProductPageResponse(BaseModel):
    """Complete response with detection and extraction results"""
    detection: ProductPageDetection
    product_info: Optional[ExtractedProductInfo] = None
    enhanced_query: Optional[str] = Field(None, description="Enhanced recommendation query based on product")
