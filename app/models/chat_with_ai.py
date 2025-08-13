from sqlalchemy import Column, ForeignKey, String, Text, TIMESTAMP, Enum, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class ChatRoleEnum(enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatWithAI(Base):
    __tablename__ = "chat_with_ai"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    scan_id = Column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(Enum(ChatRoleEnum, name="chatroleenum"), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )

    user = relationship("User")
    scan = relationship("Scan")
