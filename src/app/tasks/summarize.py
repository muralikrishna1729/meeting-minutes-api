import uuid
from app.services.celery_app import celery_app
from app.services.summarizer import get_summarizer
from app.config import settings
from app.core.statuses import MeetingStatus, TaskStatus
import pymongo

sync_mongo = pymongo.MongoClient(settings.MONGODB_URL)
db = sync_mongo[settings.MONGODB_DB]
meetings = db["meetings"]
tasks = db["tasks"]

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def summarize_meeting_task(self, meeting_id: str, original_text: str):
    meeting = meetings.find_one({"_id": meeting_id})
    if not meeting:
        return
    try:
        task = tasks.find_one({"meeting_id": meeting["_id"]})
        meetings.update_one({"_id": meeting["_id"]},
                            {"$set": {"status": MeetingStatus.PROCESSING.value}})
        result = get_summarizer().generate(original_text)
        if not result:
            raise ValueError("Summarization failed")
        meetings.update_one({"_id": meeting["_id"]}, {"$set": {
            "summary": result["summary"],
            "action_items": result["action_items"],
            "decisions": result["decisions"],
            "status": MeetingStatus.COMPLETED.value,
        }})
        if task:
            tasks.update_one({"_id": task["_id"]}, {"$set": {
                "status": TaskStatus.COMPLETED.value,
                "result": result,
            }})
    except Exception as exc:
        meetings.update_one({"_id": meeting["_id"]},
                            {"$set": {"status": MeetingStatus.FAILED.value}})
        if "task" in locals() and task:
            tasks.update_one({"_id": task["_id"]}, {"$set": {
                "status": TaskStatus.FAILED.value,
                "error": str(exc),
            }})
        raise self.retry(exc=exc)
