import faiss
import numpy as np

def build_faiss_index(vectors):
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    return index
