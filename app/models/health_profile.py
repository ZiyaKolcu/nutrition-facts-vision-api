from sqlalchemy import Column, ForeignKey, TIMESTAMP, text, String
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    allergies = Column(ARRAY(String), default=[])
    chronic_conditions = Column(ARRAY(String), default=[])
    dietary_preferences = Column(ARRAY(String), default=[])
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    user = relationship("User", back_populates="health_profile")
