import numpy as np
from typing import List
from helpers.logger import Logger, get_logger
logger = get_logger(__name__)




@staticmethod
def _cosine_similarity_matrix(embeddings_a: np.ndarray, embeddings_b: np.ndarray) -> np.ndarray:
    norm_a = np.linalg.norm(embeddings_a, axis=1, keepdims=True)
    norm_b = np.linalg.norm(embeddings_b, axis=1, keepdims=True)
    norm_a = np.where(norm_a == 0, 1, norm_a)
    norm_b = np.where(norm_b == 0, 1, norm_b)
    embeddings_a_norm = embeddings_a / norm_a
    embeddings_b_norm = embeddings_b / norm_b
    return np.dot(embeddings_a_norm, embeddings_b_norm.T)



@staticmethod
def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embedding vectors.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        arr1 = np.array(embedding1)
        arr2 = np.array(embedding2)
        
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
def find_similar_products(
        self, 
        query_embedding: List[float],
        product_embeddings: List[tuple],
        top_k: int = 10
    ) -> List[tuple]:
        """
        Find the most similar products based on embedding similarity.
        
        Args:
            query_embedding: Embedding of the query/viewed product
            product_embeddings: List of (product_id, embedding) tuples
            top_k: Number of top results to return
            
        Returns:
            List of (product_id, similarity_score) tuples, sorted by similarity
        """
        similarities = []
        
        for product_id, embedding in product_embeddings:
            similarity = self.cosine_similarity(query_embedding, embedding)
            similarities.append((product_id, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
