"""
Image-Based Product Search Service

Uses CLIP (Contrastive Language-Image Pre-Training) for visual similarity search.
Supports image-only and multi-modal (image + text) searches.
"""
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
from PIL import Image
import io
import base64
import time
import requests
from pathlib import Path

from schemas.image_search import (
    ImageEmbedding,
    VisualMatch,
    ImageSearchResponse,
    MultiModalSearchRequest
)


class ImageSearchService:
    """
    Handles image-based product search using CLIP embeddings
    """
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initialize image search service
        
        Args:
            model_name: CLIP model to use for embeddings
        """
        self.model_name = model_name
        self.model = None
        self.processor = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Load CLIP model and processor"""
        try:
            from transformers import CLIPProcessor, CLIPModel
            
            print(f"Loading CLIP model: {self.model_name}")
            self.model = CLIPModel.from_pretrained(self.model_name)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            print("CLIP model loaded successfully")
            
        except ImportError:
            print("WARNING: transformers not installed. Image search will not work.")
            print("Install with: pip install transformers torch pillow")
        except Exception as e:
            print(f"Error loading CLIP model: {e}")
    
    def encode_image(self, image: Image.Image) -> ImageEmbedding:
        """
        Generate embedding for an image
        
        Args:
            image: PIL Image
            
        Returns:
            ImageEmbedding with vector and metadata
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("CLIP model not initialized")
        
        start_time = time.time()
        
        # Process image
        inputs = self.processor(images=image, return_tensors="pt", padding=True)
        
        # Get image features
        image_features = self.model.get_image_features(**inputs)
        
        # Normalize embeddings
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        # Convert to list
        embedding = image_features[0].detach().numpy().tolist()
        
        processing_time = (time.time() - start_time) * 1000
        
        return ImageEmbedding(
            embedding=embedding,
            dimensions=len(embedding),
            model=self.model_name,
            processing_time_ms=processing_time
        )
    
    def encode_text(self, text: str) -> List[float]:
        """
        Generate embedding for text query
        
        Args:
            text: Text query
            
        Returns:
            Embedding vector
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("CLIP model not initialized")
        
        # Process text
        inputs = self.processor(text=[text], return_tensors="pt", padding=True)
        
        # Get text features
        text_features = self.model.get_text_features(**inputs)
        
        # Normalize embeddings
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        return text_features[0].detach().numpy().tolist()
    
    def load_image_from_base64(self, base64_data: str) -> Image.Image:
        """
        Load image from base64 string
        
        Args:
            base64_data: Base64 encoded image
            
        Returns:
            PIL Image
        """
        # Remove data URL prefix if present
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]
        
        image_bytes = base64.b64decode(base64_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        return image
    
    def load_image_from_url(self, url: str) -> Image.Image:
        """
        Load image from URL
        
        Args:
            url: Image URL
            
        Returns:
            PIL Image
        """
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        image = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        return image
    
    def load_image_from_path(self, path: str) -> Image.Image:
        """
        Load image from local file path
        
        Args:
            path: File path
            
        Returns:
            PIL Image
        """
        image = Image.open(path)
        
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        return image
    
    def search_by_image(
        self,
        image: Image.Image,
        product_embeddings: Dict[str, List[float]],
        product_metadata: Dict[str, Dict[str, Any]],
        max_results: int = 10,
        min_similarity: float = 0.5
    ) -> ImageSearchResponse:
        """
        Search for visually similar products
        
        Args:
            image: Query image
            product_embeddings: Dict of product_id -> embedding
            product_metadata: Dict of product_id -> metadata
            max_results: Maximum results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            ImageSearchResponse with matches
        """
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = self.encode_image(image)
        query_vector = np.array(query_embedding.embedding)
        
        # Calculate similarities
        similarities = []
        for product_id, embedding in product_embeddings.items():
            product_vector = np.array(embedding)
            
            # Cosine similarity (vectors are already normalized)
            similarity = float(np.dot(query_vector, product_vector))
            
            if similarity >= min_similarity:
                similarities.append((product_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Take top K
        top_matches = similarities[:max_results]
        
        # Build response
        matches = []
        for product_id, similarity in top_matches:
            metadata = product_metadata.get(product_id, {})
            
            match = VisualMatch(
                product_id=product_id,
                product_name=metadata.get("name", product_id),
                similarity_score=similarity,
                price=metadata.get("price"),
                category=metadata.get("category"),
                brand=metadata.get("brand"),
                image_url=metadata.get("image_url"),
                metadata=metadata
            )
            matches.append(match)
        
        search_time = (time.time() - start_time) * 1000
        
        return ImageSearchResponse(
            matches=matches,
            total_matches=len(similarities),
            query_embedding_dims=query_embedding.dimensions,
            search_time_ms=search_time,
            model_used=self.model_name
        )
    
    def multi_modal_search(
        self,
        image: Optional[Image.Image],
        text_query: Optional[str],
        product_embeddings: Dict[str, Tuple[List[float], List[float]]],
        product_metadata: Dict[str, Dict[str, Any]],
        image_weight: float = 0.5,
        text_weight: float = 0.5,
        max_results: int = 10,
        min_similarity: float = 0.5
    ) -> ImageSearchResponse:
        """
        Multi-modal search combining image and text
        
        Args:
            image: Query image (optional)
            text_query: Text query (optional)
            product_embeddings: Dict of product_id -> (image_emb, text_emb)
            product_metadata: Product metadata
            image_weight: Weight for image similarity
            text_weight: Weight for text similarity
            max_results: Maximum results
            min_similarity: Minimum similarity threshold
            
        Returns:
            ImageSearchResponse
        """
        start_time = time.time()
        
        # Generate query embeddings
        image_query_vector = None
        text_query_vector = None
        
        if image:
            image_emb = self.encode_image(image)
            image_query_vector = np.array(image_emb.embedding)
        
        if text_query:
            text_emb = self.encode_text(text_query)
            text_query_vector = np.array(text_emb)
        
        # Calculate combined similarities
        similarities = []
        for product_id, (img_emb, txt_emb) in product_embeddings.items():
            combined_similarity = 0.0
            
            # Image similarity
            if image_query_vector is not None:
                img_product_vector = np.array(img_emb)
                img_similarity = float(np.dot(image_query_vector, img_product_vector))
                combined_similarity += img_similarity * image_weight
            
            # Text similarity
            if text_query_vector is not None:
                txt_product_vector = np.array(txt_emb)
                txt_similarity = float(np.dot(text_query_vector, txt_product_vector))
                combined_similarity += txt_similarity * text_weight
            
            if combined_similarity >= min_similarity:
                similarities.append((product_id, combined_similarity))
        
        # Sort and take top K
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_matches = similarities[:max_results]
        
        # Build matches
        matches = []
        for product_id, similarity in top_matches:
            metadata = product_metadata.get(product_id, {})
            
            match = VisualMatch(
                product_id=product_id,
                product_name=metadata.get("name", product_id),
                similarity_score=similarity,
                price=metadata.get("price"),
                category=metadata.get("category"),
                brand=metadata.get("brand"),
                image_url=metadata.get("image_url"),
                metadata=metadata
            )
            matches.append(match)
        
        search_time = (time.time() - start_time) * 1000
        
        return ImageSearchResponse(
            matches=matches,
            total_matches=len(similarities),
            query_embedding_dims=512,  # CLIP default
            search_time_ms=search_time,
            model_used=self.model_name
        )
    
    def batch_encode_images(self, images: List[Image.Image]) -> List[List[float]]:
        """
        Encode multiple images in batch for efficiency
        
        Args:
            images: List of PIL Images
            
        Returns:
            List of embeddings
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("CLIP model not initialized")
        
        # Process all images
        inputs = self.processor(images=images, return_tensors="pt", padding=True)
        
        # Get image features
        image_features = self.model.get_image_features(**inputs)
        
        # Normalize
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        # Convert to list
        embeddings = image_features.detach().numpy().tolist()
        
        return embeddings


# Singleton instance
image_search_service = ImageSearchService()
