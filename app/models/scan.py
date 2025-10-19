from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_name = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_ingredients = Column(JSONB, nullable=False, default=list)
    summary_explanation = Column(Text, nullable=True)
    summary_risk = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    user = relationship("User", back_populates="scans")
    ingredients = relationship(
        "Ingredient", back_populates="scan", cascade="all, delete-orphan"
    )
    nutrients = relationship(
        "Nutrient", back_populates="scan", cascade="all, delete-orphan"
    )
