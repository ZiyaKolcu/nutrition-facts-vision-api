from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, ARRAY, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(Text, unique=True, nullable=False)
    email = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    health_profile = relationship("HealthProfile", back_populates="user", uselist=False)
    scans = relationship("Scan", back_populates="user")


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    allergies = Column(ARRAY(Text), default=[])
    chronic_conditions = Column(ARRAY(Text), default=[])
    dietary_preferences = Column(ARRAY(Text), default=[])
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="health_profile")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_name = Column(Text, nullable=False)
    barcode = Column(Text)
    image_url = Column(Text)
    raw_text = Column(Text, nullable=False)
    parsed_ingredients = Column(ARRAY(Text), nullable=False)
    summary_explanation = Column(Text)
    summary_risk = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="scans")
    ingredients = relationship("Ingredient", back_populates="scan")
    nutrients = relationship("Nutrient", back_populates="scan")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(Text, nullable=False)
    risk_level = Column(Text)

    scan = relationship("Scan", back_populates="ingredients")


class Nutrient(Base):
    __tablename__ = "nutrients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    label = Column(Text, nullable=False)
    value = Column(Numeric, nullable=False)
    max_value = Column(Numeric, nullable=False)

    scan = relationship("Scan", back_populates="nutrients")
