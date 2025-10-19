from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
import uuid

from app.db.base import Base


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    birth_of_date = Column(DateTime(timezone=True), nullable=True)
    gender = Column(String, nullable=True)
    height_cm = Column(Integer, nullable=True)
    weight_kg = Column(Integer, nullable=True)
    allergies = Column(JSONB, nullable=False, default=list)
    health_conditions = Column(JSONB, nullable=False, default=list)
    dietary_preferences = Column(JSONB, nullable=False, default=list)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )

    user = relationship("User", back_populates="health_profile")
    