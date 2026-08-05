from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import models
from app.food_estimate import estimate_query
from app.schemas import FoodEstimateIn, FoodEstimateOut

router = APIRouter()

@router.get("/api/foods")
def search_foods(q: str = "", limit: int = 20, db: Session = Depends(get_db)):
    query = db.query(models.Food)
    if q:
        query = query.filter(models.Food.name.like(f"%{q}%"))
    rows = query.limit(min(limit, 50)).all()
    return [
        {"id": f.id, "name": f.name, "source": f.source, "edible": f.edible,
         "energyKCal": f.energy_kcal, "protein": f.protein, "fat": f.fat,
         "CHO": f.carbohydrate, "dietaryFiber": f.dietary_fiber, "sodium": f.sodium}
        for f in rows
    ]


@router.post("/api/foods/estimate", response_model=FoodEstimateOut)
def estimate_foods(body: FoodEstimateIn, db: Session = Depends(get_db)):
    try:
        result = estimate_query(db, body.query)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not result["items"] and not result["unmatched"]:
        raise HTTPException(status_code=422, detail="请至少输入一种食材。")
    return result
