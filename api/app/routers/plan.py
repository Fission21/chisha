from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import models
from app.nutrition import daily_targets
from app.recommend import recommend
from app.schemas import PlanResponse, UserInput, RecipeSummary, NutritionOut, DailyTarget, MealRecommendation

router = APIRouter()

def recipe_dict(r: models.Recipe) -> dict:
    return {
        "id": r.id, "title": r.title, "titleEn": r.title_en, "cuisine": r.cuisine,
        "difficulty": r.difficulty, "cookTimeMin": r.cook_time_min, "servings": r.servings,
        "summary": r.summary, "coverEmoji": r.cover_emoji,
        "mealTypes": list(r.meal_types or []), "tags": list(r.tags or []),
        "allergens": list(r.allergens or []),
        "nutrition": {
            "energyKCal": r.energy_kcal, "protein": r.protein, "fat": r.fat,
            "CHO": r.carbohydrate, "dietaryFiber": r.dietary_fiber, "sodium": r.sodium,
        },
    }

def recipe_summary(r: models.Recipe) -> RecipeSummary:
    return RecipeSummary(**recipe_dict(r))

@router.post("/api/plan", response_model=PlanResponse)
def create_plan(body: UserInput, db: Session = Depends(get_db)):
    targets = daily_targets(body.sex, body.weight_kg, body.height_cm, body.age,
                            body.activity_level, body.goal)
    recipes = [recipe_dict(r) for r in db.query(models.Recipe).all()]
    meals = recommend(recipes, targets["daily"]["kcal"], targets["daily"]["protein"],
                      body.goal, body.allergies, body.preferred_cuisines)
    meal_out = []
    for m in meals:
        meal_out.append(MealRecommendation(
            meal=m["meal"], mealLabel=m["mealLabel"],
            targetKcal=m["targetKcal"], targetProtein=m["targetProtein"],
            recommendations=[RecipeSummary(**r) for r in m["recommendations"]],
        ))
    return PlanResponse(bmr=targets["bmr"], tdee=targets["tdee"],
                        daily=DailyTarget(**targets["daily"]), meals=meal_out)
