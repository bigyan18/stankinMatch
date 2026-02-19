import numpy as np
import logging
import pickle
from typing import Optional

# Global model variable to cache the model
_model = None

def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logging.info("Loading sentence-transformer model: all-MiniLM-L6-v2")
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logging.error(f"Failed to load sentence-transformer model: {e}")
            return None
    return _model

def get_embedding(text: str) -> Optional[bytes]:
    """
    Computes vector embedding for the given text.
    Returns bytes (pickled numpy array) or None on failure.
    """
    model = get_model()
    if model:
        try:
            embedding = model.encode(text)
            return pickle.dumps(embedding)
        except Exception as e:
            logging.error(f"Error computing embedding: {e}")
    return None

def compute_similarity(vector1_bytes: bytes, vector2_bytes: bytes) -> float:
    """
    Computes cosine similarity between two pickled vectors.
    """
    try:
        v1 = pickle.loads(vector1_bytes)
        v2 = pickle.loads(vector2_bytes)
        
        # Manual cosine similarity for speed and to avoid sklearn dependency if not needed
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
            
        return float(dot_product / (norm_v1 * norm_v2))
    except Exception as e:
        logging.error(f"Error computing similarity: {e}")
        return 0.0
