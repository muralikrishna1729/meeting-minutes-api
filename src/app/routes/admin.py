from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from pydantic import BaseModel
from app.db.session import get_db
from app.models import MeetingMinutes
from app.core.dependencies import get_current_admin
from app.config import settings
from sqlalchemy import or_

router = APIRouter(prefix="/admin", tags=["admin"])
class SwitchModelRequest(BaseModel):
    summarizer_type:str

@router.get("/stats")
async def get_admin_stats(db :AsyncSession = Depends(get_db),current_user = Depends(get_current_admin)):
    result = await db.execute(
            select(func.count()).select_from(MeetingMinutes)
            .where(MeetingMinutes.deleted_at.is_(None))

        )
    total_meetings = result.scalar()
    result = await db.execute(
            select(func.count()).select_from(MeetingMinutes)
            .where(MeetingMinutes.status == "completed")
        )
    completed = result.scalar()
    result = await db.execute(
            select(func.count()).select_from(MeetingMinutes)
            .where(MeetingMinutes.status == "failed")
        )
    failed = result.scalar()
    result = await db.execute(
            select(func.count()).select_from(MeetingMinutes)
            .where(or_(MeetingMinutes.status == "pending",MeetingMinutes.status == "processing"))
        )
    pending = result.scalar()
    return {
        "current_summarizer":settings.SUMMARIZER_TYPE,
        "total":total_meetings,
        "completed":completed,
        "failed":failed,
        "pending":pending
    }

@router.post("/model/switch")
async def switch_model(body:SwitchModelRequest,db :AsyncSession = Depends(get_db),current_user = Depends(get_current_admin)):
    if body.summarizer_type not in ["mock", "huggingface"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type"
        )
    settings.SUMMARIZER_TYPE = body.summarizer_type
    return {"message": f"Summarizer switched to {body.summarizer_type}"}