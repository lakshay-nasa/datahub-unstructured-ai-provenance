import os
import datetime
from config import Config
from ingestion.loader import load_and_chunk_file
from ingestion.pii_scanner import scan_for_pii
from storage.vector_store import save_to_chroma
from governance.datahub_client import DataHubGovernor

def run_pipeline():
    """
    Orchestrates the End-to-End RAG Pipeline:
    Discovery -> Extraction -> Inspection -> Routing -> Storage -> Governance
    """
    print(f"[*] Initializing Pipeline using Data Directory: {Config.DATA_DIR}")
    
    governor = DataHubGovernor()
    valid_extensions = ('.pdf', '.csv', '.txt', '.docx')
    
    # 1. File Discovery (Deep Traversal)
    pending_files = []
    for root, _, filenames in os.walk(Config.DATA_DIR):
        for filename in filenames:
            if filename.lower().endswith(valid_extensions):
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, Config.DATA_DIR)
                pending_files.append((full_path, rel_path))

    if not pending_files:
        print(f"[!] No valid documents found to process.")
        return

    print(f"[*] Found {len(pending_files)} documents. Beginning ingestion sequence...")

    for full_path, rel_path in pending_files:
        print(f"\n[Processing] {rel_path}")

        # 2. System Metadata Extraction (Operational Metadata)
        # Capturing raw OS level attributes before processing
        stats = os.stat(full_path)
        system_meta = {
            "file_size_kb": f"{round(stats.st_size / 1024, 2)}",
            "created_at": datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
            "extension": os.path.splitext(filename)[1].lower()
        }

        # 3. Content Ingestion (via Unstructured.io)
        text_chunks = load_and_chunk_file(full_path)
        if not text_chunks:
            print(f"   [Skipped] No text extracted.")
            continue

        # 4. Governance Policy Validation (PII Scanning)
        has_pii = False
        pii_log = []
        
        for i, chunk in enumerate(text_chunks):
            secrets = scan_for_pii(chunk)
            if secrets:
                has_pii = True
                # Log first few characters of chunk index for audit trail
                pii_log.append(f"Chunk {i}: {', '.join(secrets)}")

        # 5. Semantic Routing (The 'Sorting Hat' Logic)
        if has_pii:
            target_collection = Config.COLLECTION_SECURE
            print(f"   [!] PII DETECTED. Routing to Secure Index.")
        else:
            target_collection = Config.COLLECTION_PUBLIC
            print(f"   [OK] Content Clean. Routing to Public Index.")

        # 6. Vector Storage (ChromaDB)
        save_to_chroma(text_chunks, rel_path, target_collection)

        # 7. Metadata Publication (DataHub)
        # Emits technical, operational, and business metadata to the catalog
        governor.emit_file_metadata(
            filename=rel_path, 
            target_collection=target_collection,
            pii_details=pii_log,
            chunk_count=len(text_chunks),
            system_meta=system_meta
        ) 
        print("   [+] DataHub Lineage & Governance updated.")

    print("\n[Done] Pipeline execution complete.")

if __name__ == "__main__":
    run_pipeline()