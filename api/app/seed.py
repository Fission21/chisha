# 种子数据：将 processed JSON 导入数据库
import json
from app.db import Base, engine, SessionLocal
from app import models
from app.config import FOODS_FILE, RECIPES_FILE

def seed():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        foods = json.loads(FOODS_FILE.read_bytes().decode("utf-8-sig"))
        for f in foods:
            db.add(models.Food(
                code=f.get("code", ""), name=f.get("name", ""), source=f.get("source", ""),
                edible=f.get("edible", 100.0),
                energy_kcal=f.get("energyKCal", 0), protein=f.get("protein", 0),
                fat=f.get("fat", 0), carbohydrate=f.get("CHO", 0),
                dietary_fiber=f.get("dietaryFiber", 0), cholesterol=f.get("cholesterol", 0),
                vitamin_a=f.get("vitaminA", 0), vitamin_c=f.get("vitaminC", 0),
                vitamin_e=f.get("vitaminE", 0), calcium=f.get("Ca", 0),
                phosphorus=f.get("P", 0), potassium=f.get("K", 0), sodium=f.get("sodium", 0),
                magnesium=f.get("Mg", 0), iron=f.get("Fe", 0), zinc=f.get("Zn", 0),
                selenium=f.get("Se", 0),
            ))
        recipes = json.loads(RECIPES_FILE.read_bytes().decode("utf-8-sig"))
        for r in recipes:
            n = r.get("nutrition", {})
            db.add(models.Recipe(
                id=r["id"], title=r["title"], title_en=r.get("titleEn", ""),
                cuisine=r.get("cuisine", ""), meal_types=r.get("mealTypes", []),
                difficulty=r.get("difficulty", ""), cook_time_min=r.get("cookTimeMin", 0),
                servings=r.get("servings", 1), summary=r.get("summary", ""),
                cover_emoji=r.get("coverEmoji", ""), tags=r.get("tags", []),
                allergens=r.get("allergens", []), tips=r.get("tips", []),
                energy_kcal=n.get("energyKCal", 0), protein=n.get("protein", 0),
                fat=n.get("fat", 0), carbohydrate=n.get("CHO", 0),
                dietary_fiber=n.get("dietaryFiber", 0), sodium=n.get("sodium", 0),
            ))
            for i, ing in enumerate(r.get("ingredients", [])):
                db.add(models.RecipeIngredient(
                    recipe_id=r["id"], name=ing.get("name", ""), unit=ing.get("unit", "g"),
                    amount=ing.get("amount", 0), note=ing.get("note", ""),
                    food_name=ing.get("food", {}).get("name", ""),
                    food_source=ing.get("food", {}).get("source", ""),
                    food_code=ing.get("food", {}).get("code", ""),
                ))
            for idx, step in enumerate(r.get("steps", [])):
                db.add(models.RecipeStep(
                    recipe_id=r["id"], step_order=idx + 1, text=step.get("text", ""),
                    duration_min=step.get("durationMin"), heat=step.get("heat"),
                ))
        db.commit()
        print(f"seeded foods={len(foods)} recipes={len(recipes)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
