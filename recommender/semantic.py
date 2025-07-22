import faiss
import numpy as np

def get_top_k(query_vector, faiss_index, k=5):
    query_vector = np.array([query_vector]).astype("float32")
    distances, indices = faiss_index.search(query_vector, k)
    return indices[0], distances[0]
