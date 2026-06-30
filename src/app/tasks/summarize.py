from app.services.celery_app import celery_app
from app.services.summarizer import get_summarizer
from app.models import MeetingMinutes, Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

sync_engine = create_engine(settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def summarize_meeting_task(self, meeting_id: str, original_text: str):
    with SessionLocal() as db:
        meeting = db.query(MeetingMinutes).filter(MeetingMinutes.id == meeting_id).first()
        if not meeting:
            return
        try:
            meeting.status = "processing"
            db.commit()
            task = db.query(Task).filter(Task.meeting_id == meeting_id).first()
            result = get_summarizer().generate( original_text)
            if not result:
                raise ValueError("Summarization failed")
            meeting.summary = result["summary"]
            meeting.action_items = result["action_items"]
            meeting.decisions = result["decisions"]            
            meeting.status = "completed"
            if task:
                task.status = "SUCCESS"
                task.result = result 
            db.commit() 

        except Exception as exc:
            meeting.status = "failed"
            if task:
                task.status = "FAILURE"
                task.error = str(exc)
            db.commit()
            raise self.retry(exc=exc) 
