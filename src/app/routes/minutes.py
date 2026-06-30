import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.db.session import get_db
from app.models import MeetingMinutes, Task
from app.core.dependencies import get_current_user
from app.schemas.minutes import UploadTextRequest, MinutesResponse, StatusResponse, MinutesListResponse
from app.tasks.summarize import summarize_meeting_task

router = APIRouter(prefix="/minutes", tags=["minutes"])

@router.post("/upload-text", status_code=status.HTTP_202_ACCEPTED)
async def upload_text(body: UploadTextRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    meeting = MeetingMinutes(
        user_id=current_user.id,
        original_text=body.original_text,
        status="pending",
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    summarize_meeting_task.delay(str(meeting.id),body.original_text)

    task = Task(
        id = uuid.uuid4(),
        meeting_id=meeting.id,
        status="PENDING",
    )
    db.add(task)
    await db.commit()
    return{
        "meeting_id": meeting.id,
        "task_id": task.id,
        "status": "pending"
    }

@router.get("/{meeting_id}", response_model=MinutesResponse)
async def get_minute_by_id(meeting_id:str,db:AsyncSession=Depends(get_db), current_user = Depends(get_current_user)):
    result = await db.execute(select(MeetingMinutes).where(MeetingMinutes.id == meeting_id))
    meeting = result.scalars().first()       
    if not meeting or meeting.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting with id {meeting_id} not found"
        )
    if meeting.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this meeting")
    return meeting


@router.get("/{meeting_id}/status", response_model=StatusResponse)
async def get_minute_status(meeting_id:str,db:AsyncSession=Depends(get_db), current_user = Depends(get_current_user)):
    result = await db.execute(select(MeetingMinutes).where(MeetingMinutes.id == meeting_id))
    meeting = result.scalars().first()
    if not meeting or meeting.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting with id {meeting_id} not found"
        )
    if meeting.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this meeting")
    result = await db.execute(select(Task).where(Task.meeting_id== meeting_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting with id {meeting_id} not found"
        )
    return {
        "meeting_id": meeting.id,
        "status": meeting.status,
        "result": task.result if task else None
    }  

@router.get("/",response_model=MinutesListResponse)
async def getMinutesList(page:int=1, page_size:int=10,db:AsyncSession=Depends(get_db), current_user=Depends(get_current_user)):
    offset = (page - 1)*page_size
    count_result = await db.execute(
    select(func.count()).select_from(MeetingMinutes)
    .where(MeetingMinutes.user_id == current_user.id)
    .where(MeetingMinutes.deleted_at.is_(None))
    )
    total = count_result.scalar()

    minutes_result = await db.execute(
        select(MeetingMinutes)
        .where(MeetingMinutes.user_id == current_user.id)
        .where(MeetingMinutes.deleted_at.is_(None))
        .offset(offset).limit(page_size)
    )
    minutes = minutes_result.scalars().all()
    return MinutesListResponse(
        items=minutes,
        total=total,
        page=page,
        page_size=page_size
    )

@router.delete("/{meeting_id}",status_code=status.HTTP_204_NO_CONTENT)
async def deleteMinute(meeting_id:str,db:AsyncSession=Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(MeetingMinutes).where(MeetingMinutes.id == meeting_id))
    meeting = result.scalars().first()

    if not meeting or meeting.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    meeting.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return None




 


