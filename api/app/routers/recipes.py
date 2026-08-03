from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db import get_db
from app import models
from app.schemas import RecipeSummary, RecipeDetail, NutritionOut, IngredientOut, StepOut

router = APIRouter()

def summary(r: models.Recipe) -> RecipeSummary:
    return RecipeSummary(
        id=r.id, title=r.title, titleEn=r.title_en, cuisine=r.cuisine,
        difficulty=r.difficulty, cookTimeMin=r.cook_time_min, servings=r.servings,
        summary=r.summary, coverEmoji=r.cover_emoji, mealTypes=list(r.meal_types or []),
        tags=list(r.tags or []), allergens=list(r.allergens or []),
        nutrition=NutritionOut(energyKCal=r.energy_kcal, protein=r.protein, fat=r.fat,
                               CHO=r.carbohydrate, dietaryFiber=r.dietary_fiber, sodium=r.sodium),
    )

@router.get("/api/recipes", response_model=list[RecipeSummary])
def list_recipes(meal: str | None = None, cuisine: str | None = None, tag: str | None = None,
                 q: str | None = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(models.Recipe)
    if meal:
        query = query.filter(models.Recipe.meal_types.contains([meal]))
    if cuisine:
        query = query.filter(models.Recipe.cuisine == cuisine)
    if tag:
        query = query.filter(models.Recipe.tags.contains([tag]))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.Recipe.title.like(like), models.Recipe.title_en.like(like)))
    rows = query.limit(min(limit, 100)).all()
    return [summary(r) for r in rows]

@router.get("/api/recipes/{recipe_id}", response_model=RecipeDetail)
def get_recipe(recipe_id: str, db: Session = Depends(get_db)):
    r = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="菜谱不存在")
    return RecipeDetail(
        **summary(r).model_dump(),
        ingredients=[IngredientOut(name=i.name, unit=i.unit, amount=i.amount, note=i.note,
                                   food={"name": i.food_name, "source": i.food_source, "code": i.food_code})
                     for i in r.ingredients],
        steps=[StepOut(text=s.text, durationMin=s.duration_min, heat=s.heat) for s in r.steps],
        tips=r.tips if isinstance(r.tips, list) else [],
    )
