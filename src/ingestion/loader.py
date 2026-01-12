from unstructured.partition.auto import partition

def load_and_chunk_file(file_path):
    """
    We use Unstructured.io to automatically detect 
    file types (PDF, CSV, DOCX, TXT) and extract text content.
    """
    try:
        # 'partition' automatically detects file type (PDF, CSV, TXT, etc.)
        elements = partition(filename=file_path)
        return [str(el) for el in elements]
    except Exception as e:
        print(f" Unstructured Error: {e}")
        return []