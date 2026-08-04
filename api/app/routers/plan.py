from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import models
from app.nutrition import daily_targets
from app.recommend import recommend, recommend_week, pick_swap_recipe, MEAL_SPLIT
from app.schemas import (
    PlanResponse, UserInput, RecipeSummary, NutritionOut, DailyTarget,
    MealRecommendation, WeekDay, WeeklyPlanResponse, ShoppingItem,
    SwapIn, SwapOut,
)

router = APIRouter()

def recipe_dict(r: models.Recipe) -> dict:
    return {
        "id": r.id, "title": r.title, "titleEn": r.title_en, "cuisine": r.cuisine,
        "difficulty": r.difficulty, "complexity": r.complexity,
        "cookingMethods": list(r.cooking_methods or []),
        "equipment": list(r.equipment or []), "cookTimeMin": r.cook_time_min, "servings": r.servings,
        "summary": r.summary, "coverEmoji": r.cover_emoji,
        "mealTypes": list(r.meal_types or []), "tags": list(r.tags or []),
        "allergens": list(r.allergens or []),
        "ingredients": [
            {"name": i.name, "unit": i.unit, "amount": i.amount, "note": i.note,
             "food": {"name": i.food_name, "source": i.food_source, "code": i.food_code}}
            for i in r.ingredients
        ],
        "nutrition": {
            "energyKCal": r.energy_kcal, "protein": r.protein, "fat": r.fat,
            "CHO": r.carbohydrate, "dietaryFiber": r.dietary_fiber, "sodium": r.sodium,
        },
    }

def recipe_summary(r: models.Recipe) -> RecipeSummary:
    return RecipeSummary(**recipe_dict(r))

def aggregate_shopping(meals: list) -> list:
    agg = {}
    for m in meals:
        for r in m.get("recommendations", []):
            servings = max(1, r.get("servings", 1))
            for ing in r.get("ingredients", []):
                key = (ing.get("name", ""), ing.get("unit", "g"), ing.get("note", ""))
                amount = ing.get("amount", 0) / servings
                if key not in agg:
                    agg[key] = {"name": key[0], "unit": key[1], "note": key[2], "amount": 0.0}
                agg[key]["amount"] += amount
    items = [{"name": v["name"], "unit": v["unit"], "note": v["note"],
              "amount": round(v["amount"], 1)} for v in agg.values()]
    items.sort(key=lambda x: -x["amount"])
    return items

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
                        daily=DailyTarget(**targets["daily"]), meals=meal_out,
                        shoppingList=[ShoppingItem(**x) for x in aggregate_shopping(meals)])

@router.post("/api/weekly-plan", response_model=WeeklyPlanResponse)
def create_weekly_plan(body: UserInput, db: Session = Depends(get_db)):
    targets = daily_targets(body.sex, body.weight_kg, body.height_cm, body.age,
                            body.activity_level, body.goal)
    recipes = [recipe_dict(r) for r in db.query(models.Recipe).all()]
    result = recommend_week(recipes, targets["daily"]["kcal"], targets["daily"]["protein"],
                            body.goal, body.allergies, body.preferred_cuisines)
    today = date.today()
    days = []
    for idx, meals in enumerate(result["days"]):
        d = today + timedelta(days=idx)
        days.append(WeekDay(
            dayIndex=idx + 1,
            date=d.isoformat(),
            meals=[MealRecommendation(**m) for m in meals],
        ))
    return WeeklyPlanResponse(
        days=days,
        shoppingList=[ShoppingItem(**x) for x in result["shoppingList"]],
    )

@router.post("/api/plan/swap", response_model=SwapOut)
def swap_recipe(body: SwapIn, db: Session = Depends(get_db)):
    """换一道：同餐次、同条件重新挑一道（不重复已有），并重算购物清单。"""
    targets = daily_targets(body.user.sex, body.user.weight_kg, body.user.height_cm,
                            body.user.age, body.user.activity_level, body.user.goal)
    recipes = [recipe_dict(r) for r in db.query(models.Recipe).all()]
    split = dict((meal, value) for meal, _, value in MEAL_SPLIT).get(body.meal, 0.3)
    meal_kcal = targets["daily"]["kcal"] * split
    meal_protein = targets["daily"]["protein"] * split
    exclude = set(body.keepIds) | {body.replaceId}
    picked = pick_swap_recipe(recipes, body.meal, meal_kcal, meal_protein,
                              body.user.goal, body.user.allergies,
                              body.user.preferred_cuisines, exclude)
    if picked is None:
        return SwapOut(recipe=None,
                       shoppingList=[ShoppingItem(**x) for x in aggregate_shopping([])])
    final_ids = [rid for rid in body.keepIds if rid != body.replaceId] + [picked["id"]]
    final_recipes = [r for r in recipes if r["id"] in final_ids]
    return SwapOut(
        recipe=RecipeSummary(**picked),
        shoppingList=[ShoppingItem(**x) for x in aggregate_shopping([{"recommendations": final_recipes}])],
    )
