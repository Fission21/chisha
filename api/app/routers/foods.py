from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app import models

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
