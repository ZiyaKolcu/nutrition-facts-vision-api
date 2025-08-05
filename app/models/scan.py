from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_name = Column(String, nullable=False)
    barcode = Column(String, nullable=True)
    raw_text = Column(String, nullable=False)
    parsed_ingredients = Column(ARRAY(String), nullable=False)
    summary_explanation = Column(String, nullable=True)
    summary_risk = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    user = relationship("User", back_populates="scans")
    ingredients = relationship(
        "Ingredient", back_populates="scan", cascade="all, delete"
    )
    nutrients = relationship("Nutrient", back_populates="scan", cascade="all, delete")
