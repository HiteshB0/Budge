import json
import os
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import io

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class TransactionDraft(BaseModel):
    date: str = Field(..., description="ISO 8601 format YYYY-MM-DD")
    merchant: str = Field(..., description="Cleaned merchant name")
    amount: float
    currency: str = "USD"

class ExtractedReceipt(BaseModel):
    transactions: List[TransactionDraft]

def process_image(image_bytes: bytes) -> ExtractedReceipt:
    """Extract transactions from bank statement using Gemini Vision"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """Analyze this bank statement image and extract ALL transactions.

For EACH transaction row, extract:
1. Date (convert to YYYY-MM-DD format)
2. Merchant/Description (clean name - remove prefixes like "Payroll Deposit -", "ATM Withdrawal -", "Web Bill Payment -")
3. Amount (use the withdrawal/debit amount, ignore deposits unless specified)

Return ONLY valid JSON with NO markdown or explanation:
{"transactions": [{"date": "2003-10-14", "merchant": "HOTEL", "amount": 200.00, "currency": "USD"}]}

IMPORTANT: Extract ALL transactions visible in the image (typically 10-20 entries)."""

        # Convert bytes to PIL Image which google.generativeai prefers
        image = Image.open(io.BytesIO(image_bytes))

        response = model.generate_content([prompt, image])
        
        content = response.text.strip()
        print(f"Gemini response: {content[:300]}...")
        
        # Clean markdown if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        json_data = json.loads(content)
        return ExtractedReceipt(**json_data)

    except Exception as e:
        print(f"OCR Error: {e}")
        import traceback
        traceback.print_exc()
        return ExtractedReceipt(transactions=[])