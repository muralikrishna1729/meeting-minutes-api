from app.db.mongo import db
from app.constants import MEETINGS_COLLECTION, TASKS_COLLECTION


async def ensure_indexes() -> None:
    meetings = db[MEETINGS_COLLECTION]
    await meetings.create_index("user_id")
    await meetings.create_index("status")
    await meetings.create_index([("created_at", -1)])
    await meetings.create_index([("original_text", "text"), ("summary", "text")])  # $text

    tasks = db[TASKS_COLLECTION]
    await tasks.create_index("meeting_id", unique=True)   # preserves 1:1 invariant
