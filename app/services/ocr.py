import json
import os
import base64
import requests
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

class TransactionDraft(BaseModel):
    date: str = Field(..., description="ISO 8601 format YYYY-MM-DD")
    merchant: str = Field(..., description="Cleaned merchant name")
    amount: float
    currency: str = "INR"

class ExtractedReceipt(BaseModel):
    transactions: List[TransactionDraft]

def process_image(image_bytes: bytes) -> ExtractedReceipt:
    """Extract transactions from bank statement image using Groq Vision"""
    try:
        # Encode image to base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = """Analyze this bank statement image. Extract all visible transactions.
Return ONLY valid JSON in this format:
{
  "transactions": [
    {"date": "YYYY-MM-DD", "merchant": "Name", "amount": 123.45, "currency": "INR"}
  ]
}

Rules:
- Normalize merchant names (remove location codes)
- If year missing, assume 2025
- Ignore running balances
- Return empty array if no transactions found"""

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.2-90b-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 1000
            },
            timeout=30
        )

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            json_data = json.loads(content)
            return ExtractedReceipt(**json_data)
        else:
            print(f"Groq Vision error: {response.status_code} - {response.text}")
            return ExtractedReceipt(transactions=[])

    except Exception as e:
        print(f"OCR Error: {e}")
        return ExtractedReceipt(transactions=[])