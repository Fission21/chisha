from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db import get_db
from app import models
from app.recommend import allergens_overlap
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
        health=dict(r.health_profile or {}),
        nutrition=NutritionOut(energyKCal=r.energy_kcal, protein=r.protein, fat=r.fat,
                               CHO=r.carbohydrate, dietaryFiber=r.dietary_fiber, sodium=r.sodium),
    )

DIFFICULTY_ORDER = ["简单", "中等", "困难"]
COOKING_METHOD_ORDER = ["免火", "煎", "炒", "蒸", "煮", "炖", "焖", "卤", "烤", "拌", "搅拌", "冷藏"]
EQUIPMENT_ORDER = ["无需加热", "平底锅", "炒锅", "蒸锅", "汤锅", "烤箱", "空气炸锅", "微波炉", "电饭煲", "搅拌机", "冰箱"]
HEALTH_LABEL_ORDER = ["严格控油控盐", "高蛋白", "低油", "低钠", "低脂", "控糖", "高纤维"]

def ordered_values(values: set[str], preferred: list[str]) -> list[str]:
    return [value for value in preferred if value in values] + sorted(values - set(preferred))


def csv_values(value: str | None) -> set[str]:
    return {part.strip() for part in (value or "").split(",") if part.strip()}

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
        mealTypes=sorted({meal for r in rows for meal in (r.meal_types or [])}),
        tags=sorted({tag for r in rows for tag in (r.tags or []) if tag}),
        allergens=sorted({allergen for r in rows for allergen in (r.allergens or []) if allergen}),
        healthLabels=ordered_values(
            {label for r in rows for label in ((r.health_profile or {}).get("labels", []))},
            HEALTH_LABEL_ORDER,
        ),
    )

@router.get("/api/recipes", response_model=RecipePage | list[RecipeSummary])
def list_recipes(meal: str | None = None, cuisine: str | None = None, tag: str | None = None,
                 q: str | None = None, difficulty: str | None = None, complexity: str | None = None,
                 cooking_method: str | None = None, equipment: str | None = None,
                 equipment_mode: str = "any", health_profile: str = "balanced",
                 health_label: str | None = None, exclude_allergens: str | None = None,
                 max_kcal: float | None = Query(None, ge=0), min_protein: float | None = Query(None, ge=0),
                 max_fat: float | None = Query(None, ge=0), max_sodium: float | None = Query(None, ge=0),
                 min_fiber: float | None = Query(None, ge=0), max_added_oil: float | None = Query(None, ge=0),
                 oven: bool | None = None,
                 page: int | None = Query(None, ge=1), page_size: int = Query(12, ge=1, le=100),
                 limit: int = 50, db: Session = Depends(get_db)):
    if equipment_mode not in {"any", "all", "available"}:
        raise HTTPException(status_code=422, detail="equipment_mode 必须是 any、all 或 available")
    if health_profile not in {"balanced", "strict"}:
        raise HTTPException(status_code=422, detail="health_profile 必须是 balanced 或 strict")
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
    equipment_values = csv_values(equipment)
    if equipment_values:
        def equipment_matches(recipe):
            recipe_equipment = set(recipe.equipment or [])
            if equipment_mode == "all":
                return equipment_values.issubset(recipe_equipment)
            if equipment_mode == "available":
                required = recipe_equipment - {"无需加热"}
                return required.issubset(equipment_values)
            return bool(recipe_equipment & equipment_values)
        rows = [r for r in rows if equipment_matches(r)]
    if health_profile == "strict":
        rows = [r for r in rows if (r.health_profile or {}).get("strictEligible", False)]
    if health_label:
        rows = [r for r in rows if health_label in ((r.health_profile or {}).get("labels", []))]
    excluded = csv_values(exclude_allergens)
    if excluded:
        rows = [r for r in rows if not allergens_overlap(r.allergens or [], excluded)]
    if max_kcal is not None:
        rows = [r for r in rows if (r.energy_kcal or 0) <= max_kcal]
    if min_protein is not None:
        rows = [r for r in rows if (r.protein or 0) >= min_protein]
    if max_fat is not None:
        rows = [r for r in rows if (r.fat or 0) <= max_fat]
    if max_sodium is not None:
        rows = [r for r in rows if (r.sodium or 0) <= max_sodium]
    if min_fiber is not None:
        rows = [r for r in rows if (r.dietary_fiber or 0) >= min_fiber]
    if max_added_oil is not None:
        rows = [r for r in rows if ((r.health_profile or {}).get("addedOilG", 0) or 0) <= max_added_oil]
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
