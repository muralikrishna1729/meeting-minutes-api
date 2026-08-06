from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.dependencies import get_current_admin
from app.config import settings
from app.services.summarizer import BaseSummarizer
from app.db.mongo import db as mongo_db
from app.constants import MEETINGS_COLLECTION

router = APIRouter(prefix="/admin", tags=["admin"])
class SwitchModelRequest(BaseModel):
    summarizer_type:str

@router.get("/stats")
async def get_admin_stats(current_user = Depends(get_current_admin)):
    result = await mongo_db[MEETINGS_COLLECTION].count_documents({"deleted_at": None})
    total_meetings = result
    result = await mongo_db[MEETINGS_COLLECTION].count_documents({"status": "completed"})
    completed = result
    result = await mongo_db[MEETINGS_COLLECTION].count_documents({"status": "failed"})
    failed = result
    result = await mongo_db[MEETINGS_COLLECTION].count_documents({"status": {"$in": ["pending", "processing"]}})
    pending = result
    return {
        "current_summarizer":settings.SUMMARIZER_TYPE,
        "total":total_meetings,
        "completed":completed,
        "failed":failed,
        "pending":pending
    }

@router.post("/model/switch")
async def switch_model(body:SwitchModelRequest,current_user = Depends(get_current_admin)):
    valid_types = {cls.__name__.removesuffix("Summarizer").lower() for cls in BaseSummarizer.__subclasses__()}
    if body.summarizer_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid summarizer type"
        )
    settings.SUMMARIZER_TYPE = body.summarizer_type
    return {"message": f"Summarizer switched to {body.summarizer_type}"}