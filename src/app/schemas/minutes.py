from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class UploadTextRequest(BaseModel):
    original_text :str = Field(..., description="The original text to be uploaded.", min_length=10,max_length=50000)

class MinutesResponse(BaseModel):
    id: UUID = Field(..., description="Unique identifier for the minutes.")
    user_id: UUID = Field(..., description="Unique identifier for the user who uploaded the text.")
    status: str = Field(..., description="The status of the minutes (e.g., 'processing', 'completed', 'failed').")
    original_text: str = Field(..., description="The original text that was uploaded.")
    summary: Optional[str] = Field(None, description="The summarized version of the original text.")
    action_items: Optional[list] = Field(None, description="Action items extracted from the original text.")
    decisions: Optional[list] = Field(None, description="Decisions extracted from the original text.")
    created_at: datetime = Field(..., description="The timestamp when the minutes were created.")
    updated_at: datetime = Field(..., description="The timestamp when the minutes were last updated.")

    model_config = ConfigDict(from_attributes=True)

class StatusResponse(BaseModel):
    meeting_id :UUID 
    status:str
    result:Optional[dict]

class MinutesListResponse(BaseModel):
    items: list[MinutesResponse]
    total: int
    page: int
    page_size: int 


