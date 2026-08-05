from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db import get_db
from app import models
from app.schemas import (
    RecipeSummary, RecipeDetail, RecipePage, RecipeFacets,
    NutritionOut, IngredientOut, StepOut,
)

router = APIRouter()

def summary(r: models.Recipe) -> RecipeSummary:
    return RecipeSummary(
        id=r.id, title=r.title, titleEn=r.title_en, cuisine=r.cuisine,
        difficulty=r.difficulty, complexity=r.complexity,
        cookTimeMin=r.cook_time_min, servings=r.servings,
        summary=r.summary, coverEmoji=r.cover_emoji,
        source={"name": r.source_name or "本项目整理", "url": r.source_url or "",
                "license": r.source_license or "", "revision": r.source_revision or ""},
        mealTypes=list(r.meal_types or []),
        cookingMethods=list(r.cooking_methods or []), equipment=list(r.equipment or []),
        tags=list(r.tags or []), allergens=list(r.allergens or []),
        nutrition=NutritionOut(energyKCal=r.energy_kcal, protein=r.protein, fat=r.fat,
                               CHO=r.carbohydrate, dietaryFiber=r.dietary_fiber, sodium=r.sodium),
    )

DIFFICULTY_ORDER = ["简单", "中等", "困难"]
COOKING_METHOD_ORDER = ["免火", "煎", "炒", "蒸", "煮", "炖", "焖", "卤", "烤", "拌", "搅拌", "冷藏"]
EQUIPMENT_ORDER = ["无需加热", "平底锅", "炒锅", "蒸锅", "汤锅", "烤箱", "电饭煲", "搅拌机", "冰箱"]

def ordered_values(values: set[str], preferred: list[str]) -> list[str]:
    return [value for value in preferred if value in values] + sorted(values - set(preferred))

def recipe_facets(db: Session) -> RecipeFacets:
    rows = db.query(models.Recipe).all()
    return RecipeFacets(
        cuisines=sorted({r.cuisine for r in rows if r.cuisine}),
        difficulties=ordered_values({r.difficulty for r in rows if r.difficulty}, DIFFICULTY_ORDER),
        cookingMethods=ordered_values(
            {method for r in rows for method in (r.cooking_methods or [])}, COOKING_METHOD_ORDER,
        ),
        equipment=ordered_values(
            {item for r in rows for item in (r.equipment or [])}, EQUIPMENT_ORDER,
        ),
    )

@router.get("/api/recipes", response_model=RecipePage | list[RecipeSummary])
def list_recipes(meal: str | None = None, cuisine: str | None = None, tag: str | None = None,
                 q: str | None = None, difficulty: str | None = None, complexity: str | None = None,
                 cooking_method: str | None = None, equipment: str | None = None, oven: bool | None = None,
                 page: int | None = Query(None, ge=1), page_size: int = Query(12, ge=1, le=100),
                 limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(models.Recipe).order_by(models.Recipe.title.asc(), models.Recipe.id.asc())
    if cuisine:
        query = query.filter(models.Recipe.cuisine == cuisine)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.Recipe.title.like(like), models.Recipe.title_en.like(like)))
    # JSON 数组字段（meal/tag）取回后在内存过滤，兼容 SQLite 与 PostgreSQL
    rows = query.all()
    if meal:
        rows = [r for r in rows if meal in (r.meal_types or [])]
    if tag:
        rows = [r for r in rows if tag in (r.tags or [])]
    if difficulty:
        rows = [r for r in rows if r.difficulty == difficulty]
    if complexity:
        rows = [r for r in rows if r.complexity == complexity]
    if cooking_method:
        rows = [r for r in rows if cooking_method in (r.cooking_methods or [])]
    if equipment:
        rows = [r for r in rows if equipment in (r.equipment or [])]
    if oven is not None:
        rows = [r for r in rows if ("烤箱" in (r.equipment or [])) == oven]

    # 不带 page 时继续返回旧数组，供日记搜索等轻量调用使用；菜谱库显式使用分页对象。
    if page is None:
        rows = rows[: min(max(limit, 0), 100)]
        return [summary(r) for r in rows]

    total = len(rows)
    start = (page - 1) * page_size
    page_rows = rows[start:start + page_size]
    return RecipePage(
        items=[summary(r) for r in page_rows],
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=(total + page_size - 1) // page_size,
        facets=recipe_facets(db),
    )

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
