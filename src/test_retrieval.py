import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from config import Config

# 1. Setup the same Local Embedding logic (Must match ingestion!)
print("[*] Loading Local Embedding Model (BAAI/bge-small-en-v1.5)...")
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# 2. Connect to the Disk Database
chroma_client = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)

def perform_retrieval_test(index_name, query_text):
    """
    Executes a semantic search against a specific Vector Index.
    Used to validate that data was correctly routed and is retrievable.
    """
    print(f"\n Testing Index: '{index_name}'")
    print(f"   Query: {query_text}")

    # Get the specific collection
    try:
        chroma_collection = chroma_client.get_collection(index_name)
    except Exception:
        print(f"   Target Index '{index_name}' not found! Did you run ingestion?")
        return

    # Load it into LlamaIndex
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=Settings.embed_model
    )

    # Create a retriever (Not a chatbot, just a fetcher)
    retriever = index.as_retriever(similarity_top_k=1)
    results = retriever.retrieve(query_text)

    if results:
        print(f"   ✅ Found Match! (Score: {results[0].score:.2f})")
        print(f"    * Content: {results[0].text[:200]}...") # Show first 200 chars
        print(f"    * Source: {results[0].metadata['source']}")
    else:
        print("   ❌ No relevant data found.")

if __name__ == "__main__":
    # --- SCENARIO 1: PUBLIC DOMAIN RETRIEVAL ---
    print("\n--- TESTING PUBLIC KNOWLEDGE BASE ---")
    perform_retrieval_test(Config.COLLECTION_PUBLIC, "What are the core business risks mentioned in the reports?")
    perform_retrieval_test(Config.COLLECTION_PUBLIC, "Give me details about the filing entities.")

    # --- SCENARIO 2: RESTRICTED DOMAIN RETRIEVAL ---
    print("\n--- TESTING SECURE RESTRICTED INDEX ---")
    perform_retrieval_test(Config.COLLECTION_SECURE, "What is the IBAN number for the payment?")
    perform_retrieval_test(Config.COLLECTION_SECURE, "What is the phone number of the candidate?")

    # --- TEST 3: THE COMPLIANCE CHECK (CROSS-QUERY) ---
    print("\n--- COMPLIANCE CROSS CHECK ---")
    # We ask the PUBLIC index for a SECRET. It should NOT find it.
    # It might find a random "safe" page, but not the actual credit card.
    perform_retrieval_test(Config.COLLECTION_PUBLIC, "Show me the credit card details for Invoice 1.")