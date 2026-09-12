"""
Database models for MayoMandi.
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, func
from .database import Base


class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    rice_grams = Column(Float, index=True)
    spice_level = Column(String, default="medium")
    dryness = Column(String, default="normal")
    mayo_preference = Column(String, default="balanced")
    recommended_mayo = Column(Float)
    uselessness_score = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now())
