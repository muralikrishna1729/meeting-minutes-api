from enum import Enum
class MeetingStatus(str, Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    IN_PROGRESS = 'in_progress'
    FAILED = 'failed'

class TaskStatus(str, Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    IN_PROGRESS = 'in_progress'
    FAILED = 'failed'
