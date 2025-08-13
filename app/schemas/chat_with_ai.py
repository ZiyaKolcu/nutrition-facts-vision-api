from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Literal, List


class ChatWithAICreate(BaseModel):
    user_id: UUID
    scan_id: UUID
    role: Literal["user", "assistant"]
    message: str


class ChatWithAIRead(BaseModel):
    id: UUID
    user_id: UUID
    scan_id: UUID
    role: str
    message: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    """Incoming chat message payload."""

    message: str


class ChatPostResponse(BaseModel):
    """Response for POST chat containing the user and assistant messages."""

    messages: List[ChatWithAIRead]
