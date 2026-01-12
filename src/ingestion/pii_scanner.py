from presidio_analyzer import AnalyzerEngine

# We limit the analysis chunk size to prevent NLP model memory overflows (spaCy limit).
MAX_ANALYSIS_CHUNK_SIZE = 500_000

# Entities relevant to PII Governance ( Feel free to updated based on your usecase )
TARGET_ENTITIES = ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD", "IBAN_CODE"]

# Minimum confidence score (0.0 to 1.0) to report a finding.
# Lowered to 0.4 to catch 'fuzzy' matches in OCR'd documents.
CONFIDENCE_THRESHOLD = 0.4

# Initialize the NLP engine once at module level to avoid reload overhead
_analyzer = AnalyzerEngine()

def scan_for_pii(text_content: str) -> list[str]:
    """
    Analyzes text for sensitive PII entities using Microsoft Presidio.

    Args:
        text_content (str): The raw string extracted from a document.
        
    Returns:
        list[str]: Unique list of detected entity types (e.g. ['US_SSN', 'CREDIT_CARD']).
    """
    # Fail fast on empty or trivial input
    if not text_content or not isinstance(text_content, str) or len(text_content.strip()) < 5:
        return []

    detected_entities = set()

    # Generator to slice text into safe memory chunks
    chunks = (
        text_content[i : i + MAX_ANALYSIS_CHUNK_SIZE] 
        for i in range(0, len(text_content), MAX_ANALYSIS_CHUNK_SIZE)
    )

    for chunk in chunks:
        try:
            results = _analyzer.analyze(
                text=chunk, 
                entities=TARGET_ENTITIES, 
                language='en'
            )
            
            for result in results:
                if result.score >= CONFIDENCE_THRESHOLD:
                    detected_entities.add(result.entity_type)

        except Exception as e:
            print(f"   [!] PII Scan Warning: Sub chunk analysis failed ({e})")

    return list(detected_entities)