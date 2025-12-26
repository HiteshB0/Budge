from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import ocr

router = APIRouter()

@router.post("/upload")
async def upload_screenshot(
    file: UploadFile,
    db: Session = Depends(get_db)
):
    image_bytes = await file.read()
    result = ocr.process_image(image_bytes)
    return {"status": "success", "transactions_found": len(result.transactions), "data": result}