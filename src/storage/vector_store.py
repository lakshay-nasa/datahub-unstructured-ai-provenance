import logging
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, Document, StorageContext, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from config import Config

# --- Service Initialization ---

# 1. Suppressing Telemetry & Verbose Logs
# ChromaDB and HuggingFace can be noisy; we restrict logs to Errors only for a clean CLI.
logging.getLogger("chromadb").setLevel(logging.ERROR)

# 2. Configuring Local Embeddings (Privacy-First)
# We are using 'BAAI/bge-small-en-v1.5', a high performance local model.
# This ensures data never leaves the local environment for vectorization.
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# 3. Initialize Persistent Database Connection
# We initialize the client at the module level to maintain a connection pool.
_chroma_client = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)

def save_to_chroma(text_chunks: list[str], filename: str, collection_name: str):
    """
    Vectorizes text chunks and persists them into the specified ChromaDB collection.
    
    Args:
        text_chunks (list[str]): The raw text content to index.
        filename (str): Source identifier for metadata (lineage tracking).
        collection_name (str): The target 'Wardrobe' (Secure or Public).
    """
    if not text_chunks:
        return

    try:
        # 1. entity Selection
        # Get or create the specific collection for this security level
        chroma_collection = _chroma_client.get_or_create_collection(collection_name)
        
        # 2. LlamaIndex Bridge
        # Wrap ChromaDB in a LlamaIndex VectorStore adapter
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # 3. Document Construction
        # Convert raw strings into LlamaIndex Document objects with source metadata
        documents = [
            Document(
                text=chunk, 
                metadata={"source": filename}
            ) for chunk in text_chunks
        ]

        # 4. Ingestion & Embedding
        # This step calculates vectors (using BAAI model) and writes to disk.
        # We use 'from_documents' to  handle the insertion logic.
        VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context
        )
        
        print(f"   [+] Indexed {len(documents)} chunks into '{collection_name}'")

    except Exception as e:
        print(f"   [!] Database Error: Could not save to {collection_name} ({e})")