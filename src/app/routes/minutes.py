import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.schemas.minutes import UploadTextRequest, MinutesResponse, StatusResponse, MinutesListResponse
from app.tasks.summarize import summarize_meeting_task
from app.core.statuses import MeetingStatus, TaskStatus
from app.db.mongo import db as mongo_db
from app.constants import MEETINGS_COLLECTION, TASKS_COLLECTION

meetings = mongo_db[MEETINGS_COLLECTION]
tasks = mongo_db[TASKS_COLLECTION]

router = APIRouter(prefix="/minutes", tags=["minutes"])

@router.post("/upload-text", status_code=status.HTTP_202_ACCEPTED)
async def upload_text(body: UploadTextRequest, current_user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    meeting_dict = {
        "_id": str(uuid.uuid4()),
        "original_text": body.original_text,
        "user_id": str(current_user.id),
        "status": MeetingStatus.PENDING.value,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    await mongo_db[MEETINGS_COLLECTION].insert_one(meeting_dict)
    summarize_meeting_task.delay(str(meeting_dict["_id"]),body.original_text)
    task = {
        "_id": str(uuid.uuid4()),
        "meeting_id": meeting_dict["_id"],
        "status": TaskStatus.PENDING.value,
        "result": None,
    }
    await tasks.insert_one(task)
    return {
        "meeting_id": str(meeting_dict["_id"]),
        "task_id": str(task["_id"]),
        "status": meeting_dict["status"],
        "message": "Meeting text uploaded successfully. Processing has started."
    }    

@router.get("/{meeting_id}", response_model=MinutesResponse)
async def get_minute_by_id(meeting_id:str, current_user = Depends(get_current_user)):
    meeting = await mongo_db[MEETINGS_COLLECTION].find_one({"_id": meeting_id})
    if not meeting or meeting.get("deleted_at") is not None:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting with id {meeting_id} not found"
        )
    if meeting["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this meeting")
    return meeting


@router.get("/{meeting_id}/status", response_model=StatusResponse)
async def get_minute_status(meeting_id:str, current_user = Depends(get_current_user)):
    meeting = await mongo_db[MEETINGS_COLLECTION].find_one({"_id": meeting_id})
    if not meeting or meeting.get("deleted_at") is not None:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting with id {meeting_id} not found"
        )
    if meeting["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this meeting")
    task = await tasks.find_one({"meeting_id": meeting["_id"]})
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting with id {meeting_id} not found"
        )
    return {
        "meeting_id": meeting["_id"],
        "status": meeting["status"],
        "result": task["result"] if task else None
    }  

@router.get("/",response_model=MinutesListResponse)
async def getMinutesList(page:int=1, page_size:int=10, q:str | None = None, current_user=Depends(get_current_user)):
    skip = (page - 1)*page_size
    filter_query = {"user_id": str(current_user.id), "deleted_at": None}
    if q:
        filter_query["$text"] = {"$search":q }
    total = await mongo_db[MEETINGS_COLLECTION].count_documents(filter_query)
    cursor = mongo_db[MEETINGS_COLLECTION].find(filter_query).sort("created_at", -1).skip(skip).limit(page_size)
    minutes = await cursor.to_list(length=page_size)
    return MinutesListResponse(
        items=minutes,
        total=total,
        page=page,
        page_size=page_size
    )

@router.delete("/{meeting_id}",status_code=status.HTTP_204_NO_CONTENT)
async def deleteMinute(meeting_id:str, current_user=Depends(get_current_user)):
    meeting = await mongo_db[MEETINGS_COLLECTION].find_one({"_id": meeting_id})
    if not meeting or meeting.get("deleted_at") is not None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    await mongo_db[MEETINGS_COLLECTION].update_one({"_id": meeting["_id"]}, {"$set": {"deleted_at": datetime.now(timezone.utc)}})
    return None