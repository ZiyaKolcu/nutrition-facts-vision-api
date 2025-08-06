from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    user = relationship("User", back_populates="scans")
    ingredients = relationship(
        "Ingredient", back_populates="scan", cascade="all, delete-orphan"
    )
    nutrients = relationship(
        "Nutrient", back_populates="scan", cascade="all, delete-orphan"
    )
