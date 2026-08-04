from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict

# ---------- 计划 / 菜谱 ----------
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
    complexity: str
    cookingMethods: List[str]
    equipment: List[str]
    cookTimeMin: int
    servings: int
    summary: str
    coverEmoji: str
    mealTypes: List[str]
    tags: List[str]
    allergens: List[str]
    nutrition: NutritionOut

class RecipeFacets(BaseModel):
    cuisines: List[str]
    difficulties: List[str]
    cookingMethods: List[str]
    equipment: List[str]

class RecipePage(BaseModel):
    items: List[RecipeSummary]
    total: int
    page: int
    pageSize: int
    totalPages: int
    facets: RecipeFacets

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

class ShoppingItem(BaseModel):
    name: str
    amount: float
    unit: str
    note: str = ""

class PlanResponse(BaseModel):
    bmr: float
    tdee: float
    daily: DailyTarget
    meals: List[MealRecommendation]
    shoppingList: List[ShoppingItem] = Field(default_factory=list)

class WeekDay(BaseModel):
    dayIndex: int
    date: str
    meals: List[MealRecommendation]

class WeeklyPlanResponse(BaseModel):
    days: List[WeekDay]
    shoppingList: List[ShoppingItem]

class SwapIn(BaseModel):
    meal: str
    replaceId: str
    keepIds: List[str] = Field(default_factory=list)
    user: UserInput

class SwapOut(BaseModel):
    recipe: Optional[RecipeSummary] = None
    shoppingList: List[ShoppingItem] = Field(default_factory=list)

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

# ---------- 认证 ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=64)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    token: str
    email: str

class ProfileIn(BaseModel):
    sex: str = "male"
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    body_fat: Optional[float] = None
    activity_level: str = "moderate"
    goal: str = "maintain"
    allergies: List[str] = Field(default_factory=list)
    preferred_cuisines: List[str] = Field(default_factory=list)

class ProfileOut(ProfileIn):
    pass

class FavoritesIn(BaseModel):
    ids: List[str] = Field(default_factory=list)

class DiaryIn(BaseModel):
    date: str
    items: List[dict] = Field(default_factory=list)
