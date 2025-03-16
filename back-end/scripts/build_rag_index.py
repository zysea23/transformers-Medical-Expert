# scripts/build_rag_index.py
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.medrag.medrag import MedRAG
from app.models.medrag.utils import Retriever, RetrievalSystem

def build_index():
    print("Starting to build MedRAG index...")
    print("This process may take a few minutes, please be patient...")
    
    # Initialize the retriever, which will trigger index building
    retriever = Retriever(
        retriever_name="ncbi/MedCPT-Query-Encoder",
        corpus_name="textbooks",
        db_dir="./corpus",
        HNSW=True  # Use Hierarchical Navigable Small World graph index for faster retrieval
    )
    
    print(f"Index has been successfully built and saved to: {retriever.index_dir}")
    print("You can now set corpus_cache=False to save memory usage")

if __name__ == "__main__":
    build_index()