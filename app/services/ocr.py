import json
import os
import google.generativeai as genai
from app.schemas.ingest import ExtractedReceipt
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

response_schema = {
    "type": "object",
    "properties": {
        "transactions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "ISO 8601 format YYYY-MM-DD"},
                    "merchant": {"type": "string", "description": "Normalized merchant name"},
                    "amount": {"type": "number"},
                    "currency": {"type": "string"}
                },
                "required": ["date", "merchant", "amount"]
            }
        }
    }
}

def process_image(image_bytes: bytes) -> ExtractedReceipt:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": response_schema
            }
        )
        prompt = """
        Analyze this bank statement image. 
        Extract all visible transactions.
        Normalize merchant names (e.g., remove 'NY #1234' from 'Starbucks').
        If the year is missing, assume the current year.
        Ignore running balances.
        """

        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])

        json_content = json.loads(response.text)
        return ExtractedReceipt(**json_content)

    except Exception as e:
        print(f"Gemini OCR Error: {e}")
        return ExtractedReceipt(transactions=[])