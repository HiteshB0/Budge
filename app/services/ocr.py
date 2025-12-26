import json
import os
from google import genai
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class TransactionDraft(BaseModel):
    date: str = Field(..., description="ISO 8601 format YYYY-MM-DD")
    merchant: str = Field(..., description="Cleaned merchant name")
    amount: float
    currency: str = "INR"

class ExtractedReceipt(BaseModel):
    transactions: List[TransactionDraft]

response_schema = {
    "type": "OBJECT",
    "properties": {
        "transactions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "date": {
                        "type": "STRING",
                        "description": "ISO 8601 format YYYY-MM-DD"
                    },
                    "merchant": {
                        "type": "STRING",
                        "description": "Normalized merchant name"
                    },
                    "amount": {
                        "type": "NUMBER"
                    },
                    "currency": {
                        "type": "STRING"
                    }
                },
                "required": ["date", "merchant", "amount"]
            }
        }
    },
    "required": ["transactions"]
}

def process_image(image_bytes: bytes) -> ExtractedReceipt:
    try:
        prompt = """
        Analyze this bank statement image. 
        Extract all visible transactions.
        Normalize merchant names (e.g., remove 'NY #1234' from 'Starbucks').
        If the year is missing, assume the current year (2025).
        Ignore running balances.
        Return ONLY valid JSON matching the schema.
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[
                prompt,
                {"mime_type": "image/jpeg", "data": image_bytes}
            ],
            config=genai.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )

        json_content = json.loads(response.text)
        return ExtractedReceipt(**json_content)

    except Exception as e:
        print(f"Gemini OCR Error: {e}")
        return ExtractedReceipt(transactions=[])