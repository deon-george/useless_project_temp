from pydantic import BaseModel, Field
from typing import Optional, List


class CalculationRequest(BaseModel):
    rice_grams: float = Field(..., gt=0, description="Amount of mandi rice in grams")
    spice_level: str = Field(
        default="medium",
        description="Spice level: mild, medium, spicy, nuclear",
    )
    dryness: str = Field(
        default="normal",
        description="Dryness level: moist, normal, dry, sahara",
    )
    mayo_preference: str = Field(
        default="balanced",
        description="Mayo preference: minimal, balanced, lover, criminal",
    )


class BreakdownItem(BaseModel):
    step: str
    amount: float
    unit: str


class CalculationResponse(BaseModel):
    rice_grams: float
    base_mayo: float
    spice_factor: float
    dryness_factor: float
    preference_factor: float
    recommended_mayo_grams: float
    ratio: str
    tablespoons: int
    uselessness_score: int
    breakdown: List[BreakdownItem]
    verdict: str
    verdict_color: str


class ReverseRequest(BaseModel):
    mayo_grams: float = Field(..., gt=0, description="Amount of mayo available in grams")
    spice_level: str = Field(default="medium")
    dryness: str = Field(default="normal")
    mayo_preference: str = Field(default="balanced")


class ReverseResponse(BaseModel):
    mayo_grams: float
    recommended_rice_grams: float
    potential_servings: int
    mayo_sustainability: str
    ratio: str

