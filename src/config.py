import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Central configuration for the DataHub AI Governance Pipeline.
    Manages service endpoints, storage paths, and vector index definitions.
    """
    DATAHUB_URL = os.getenv("DATAHUB_API_URL", "http://localhost:8080")
    DATAHUB_TOKEN = os.getenv("DATAHUB_ACCESS_TOKEN")
    CHROMA_DB_PATH = os.path.join(os.getcwd(), "chroma_db_storage")
    COLLECTION_PUBLIC = "public_knowledge_base"
    COLLECTION_SECURE = "secure_restricted_index"
    
    # --- Local File System ---
    DATA_DIR = os.path.join(os.getcwd(), "data", "source")
    PROCESSED_DIR = os.path.join(os.getcwd(), "data", "processed")

for directory in [Config.DATA_DIR, Config.PROCESSED_DIR, Config.CHROMA_DB_PATH]:
    os.makedirs(directory, exist_ok=True)