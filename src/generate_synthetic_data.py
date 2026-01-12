import os
import random
from faker import Faker
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from config import Config

# Initialize Faker with US localization to generate valid-looking PII (SSN, etc.)
data_gen = Faker('en_US')

def generate_hr_document(filename, include_sensitive_data=True):
    """
    Generates a synthetic Candidate Profile (Resume).
    Used to validate PII detection logic for HR use cases.
    
    Args:
        filename (str): Output file path.
        include_sensitive_data (bool): If True, injects SSN/Phone to trigger compliance alerts.
    """
    c = canvas.Canvas(filename, pagesize=LETTER)
    width, height = LETTER
    
    # 1. Header (Candidate Name)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, data_gen.name())
    
    # 2. Contact Information
    c.setFont("Helvetica", 10)
    y_position = height - 70
    
    if include_sensitive_data:
        # Inject High Risk PII (Simulating a data leak or unredacted file)
        c.drawString(50, y_position, f"Email: {data_gen.email()}")
        c.drawString(50, y_position - 15, f"Phone: {data_gen.phone_number()}")
        c.drawString(50, y_position - 30, f"SSN: {data_gen.ssn()}") # <--- Compliance Trigger
        c.drawString(50, y_position - 45, f"Address: {data_gen.address().replace('\n', ', ')}")
        y_position -= 60
    else:
        # Inject Low Risk / Public Info (Simulating a clean profile)
        c.drawString(50, y_position, "LinkedIn: linkedin.com/in/candidate")
        c.drawString(50, y_position - 15, "Location: Remote")
        y_position -= 30

    # 3. Professional Summary
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position - 20, "Professional Summary")
    c.setFont("Helvetica", 10)
    
    summary = data_gen.paragraph(nb_sentences=5)
    c.drawString(50, y_position - 40, summary[:90])
    c.drawString(50, y_position - 55, summary[90:180])
    
    c.save()
    print(f"   [+] Generated HR Artifact: {os.path.basename(filename)} | Risk Level: {'HIGH' if include_sensitive_data else 'LOW'}")

def generate_finance_document(filename, is_confidential=False):
    """
    Generates a synthetic Financial Record.
    Used to validate 'Secure' vs 'Public' routing logic.
    """
    c = canvas.Canvas(filename, pagesize=LETTER)
    width, height = LETTER
    
    # 1. Document Header
    c.setFont("Helvetica-Bold", 16)
    doc_type = "CLIENT INVOICE" if is_confidential else "PUBLIC POLICY DOCUMENT"
    c.drawString(50, height - 50, f"{doc_type} - {data_gen.year()}")
    
    # 2. Metadata
    c.setFont("Helvetica", 10)
    y = height - 80
    c.drawString(50, y, f"Reference ID: {data_gen.uuid4()}")
    y -= 20
    
    # 3. Body Content
    if is_confidential:
        # Inject Regulated Financial Data (PCI-DSS Context)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "PAYMENT DETAILS (CONFIDENTIAL):")
        y -= 20
        c.setFont("Helvetica", 10)
        
        c.drawString(50, y, f"Client Name: {data_gen.name()}")
        c.drawString(50, y-15, f"Credit Card: {data_gen.credit_card_number()}") 
        c.drawString(50, y-30, f"IBAN: {data_gen.iban()}") 
        c.drawString(50, y-45, f"Billing Address: {data_gen.address().replace('\n', ', ')}")
    else:
        # Inject Benign Corporate Text
        c.setFont("Helvetica", 10)
        c.drawString(50, y, "Subject: General Usage Guidelines")
        y -= 20
        
        text = data_gen.paragraph(nb_sentences=8)
        c.drawString(50, y, text[:90])
        c.drawString(50, y-15, text[90:])

    c.save()
    print(f"   [+] Generated Finance Artifact: {os.path.basename(filename)} | Risk Level: {'HIGH' if is_confidential else 'LOW'}")

if __name__ == "__main__":
    print("[*] Initializing Synthetic Data Generation Sequence...")
    
    if not os.path.exists(Config.DATA_DIR):
        os.makedirs(Config.DATA_DIR)
        print(f"   [+] Created source directory: {Config.DATA_DIR}")

    # 1. Generate HR Domain Data
    # Simulates a mix of 'Redacted' (Safe) and 'Unredacted' (Risky) resumes
    for i in range(1, 4):
        generate_hr_document(os.path.join(Config.DATA_DIR, f"Resume_Risky_{i}.pdf"), include_sensitive_data=True)
    for i in range(1, 3):
        generate_hr_document(os.path.join(Config.DATA_DIR, f"Resume_Safe_{i}.pdf"), include_sensitive_data=False)

    # 2. Generate Finance Domain Data
    # Simulates mixed document types to test semantic routing
    for i in range(1, 6):
        generate_finance_document(os.path.join(Config.DATA_DIR, f"Invoice_Confidential_{i}.pdf"), is_confidential=True)
    for i in range(1, 6):
        generate_finance_document(os.path.join(Config.DATA_DIR, f"Policy_Public_{i}.pdf"), is_confidential=False)
        
    print(f"\n[OK] Generation Complete. 16 Synthetic Artifacts ready for ingestion.")