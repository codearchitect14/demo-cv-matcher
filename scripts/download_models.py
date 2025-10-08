"""
Script to pre-download required ML models for offline use.
Run this script when you have internet connection to cache models locally.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def download_sentence_transformer_model(model_name: str = "all-MiniLM-L6-v2"):
    """Download sentence transformer model to local cache"""
    try:
        from sentence_transformers import SentenceTransformer
        
        print(f"Downloading model: {model_name}")
        print(f"This may take a few minutes depending on your internet connection...")
        
        # Download the model (will be cached in ~/.cache/torch/sentence_transformers/)
        model = SentenceTransformer(model_name)
        
        print(f"\n✓ Successfully downloaded model: {model_name}")
        print(f"  - Embedding dimension: {model.get_sentence_embedding_dimension()}")
        print(f"  - Max sequence length: {model.max_seq_length}")
        print(f"\nModel cached at: ~/.cache/torch/sentence_transformers/{model_name}")
        print(f"\nYou can now run your application offline!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to download model: {e}")
        print(f"\nPlease check your internet connection and try again.")
        return False

def verify_model_cache(model_name: str = "all-MiniLM-L6-v2"):
    """Verify if model is available in local cache"""
    try:
        from sentence_transformers import SentenceTransformer
        
        print(f"Verifying local cache for model: {model_name}")
        
        # Try to load from cache only
        model = SentenceTransformer(model_name, local_files_only=True)
        
        print(f"\n✓ Model found in local cache!")
        print(f"  - Embedding dimension: {model.get_sentence_embedding_dimension()}")
        print(f"  - Max sequence length: {model.max_seq_length}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Model not found in local cache: {e}")
        print(f"Run this script to download it.")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download ML models for offline use")
    parser.add_argument(
        "--model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Model name to download (default: all-MiniLM-L6-v2)"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify if model exists in cache, don't download"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Model Download/Verification Script")
    print("=" * 60)
    print()
    
    if args.verify_only:
        verify_model_cache(args.model)
    else:
        # First verify
        if verify_model_cache(args.model):
            print("\nModel already cached. No download needed.")
        else:
            print("\nAttempting to download model...")
            download_sentence_transformer_model(args.model)
    
    print()
    print("=" * 60)

