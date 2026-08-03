from pydantic import BaseModel, Field
from typing import List, Optional

class UserInput(BaseModel):
    sex: str = Field(..., description="male/female")
    age: int = Field(..., ge=10, le=100)
    height_cm: float = Field(..., ge=100, le=250)
    weight_kg: float = Field(..., ge=30, le=300)
    body_fat: Optional[float] = Field(None, ge=3, le=70)
    activity_level: str = Field("moderate", description="sedentary/light/moderate/active/very")
    goal: str = Field("maintain", description="cut/bulk/maintain")
    allergies: List[str] = Field(default_factory=list)
    preferences: List[str] = Field(default_factory=list)
    preferred_cuisines: List[str] = Field(default_factory=list)

class NutritionOut(BaseModel):
    energyKCal: float
    protein: float
    fat: float
    CHO: float
    dietaryFiber: float
    sodium: float

class RecipeSummary(BaseModel):
    id: str
    title: str
    titleEn: str
    cuisine: str
    difficulty: str
    cookTimeMin: int
    servings: int
    summary: str
    coverEmoji: str
    mealTypes: List[str]
    tags: List[str]
    allergens: List[str]
    nutrition: NutritionOut

class MealRecommendation(BaseModel):
    meal: str
    mealLabel: str
    targetKcal: float
    targetProtein: float
    recommendations: List[RecipeSummary]

class DailyTarget(BaseModel):
    kcal: float
    protein: float
    fat: float
    carb: float
    fiber: float

class PlanResponse(BaseModel):
    bmr: float
    tdee: float
    daily: DailyTarget
    meals: List[MealRecommendation]

class IngredientOut(BaseModel):
    name: str
    unit: str
    amount: float
    note: str
    food: dict

class StepOut(BaseModel):
    text: str
    durationMin: Optional[int] = None
    heat: Optional[str] = None

class RecipeDetail(RecipeSummary):
    ingredients: List[IngredientOut]
    steps: List[StepOut]
    tips: List[str]
