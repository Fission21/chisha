# 种子数据：将 processed JSON 导入数据库
import json
from sqlalchemy import inspect, text
from app.db import Base, engine, SessionLocal
from app import models
from app.config import FOODS_FILE, RECIPES_FILE

def ensure_recipe_metadata_columns():
    columns = {column["name"] for column in inspect(engine).get_columns("recipes")}
    missing = {"cooking_methods", "equipment", "complexity"} - columns
    if not missing:
        return
    with engine.begin() as conn:
        if "cooking_methods" in missing:
            conn.execute(text("ALTER TABLE recipes ADD COLUMN cooking_methods JSON"))
        if "equipment" in missing:
            conn.execute(text("ALTER TABLE recipes ADD COLUMN equipment JSON"))
        if "complexity" in missing:
            conn.execute(text("ALTER TABLE recipes ADD COLUMN complexity VARCHAR(8) DEFAULT ''"))

def seed():
    # 幂等：只建表，已有菜谱数据则跳过（不覆盖用户数据）
    Base.metadata.create_all(engine)
    ensure_recipe_metadata_columns()
    db = SessionLocal()
    try:
        recipes = json.loads(RECIPES_FILE.read_bytes().decode("utf-8-sig"))
        if db.query(models.Recipe).count() > 0:
            metadata = {r["id"]: r for r in recipes}
            for row in db.query(models.Recipe).all():
                source = metadata.get(row.id)
                if source:
                    row.cooking_methods = source.get("cookingMethods", [])
                    row.equipment = source.get("equipment", [])
                    row.complexity = source.get("complexity", "")
            db.commit()
            print("数据库已有数据，跳过种子导入")
            return
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
        for r in recipes:
            n = r.get("nutrition", {})
            db.add(models.Recipe(
                id=r["id"], title=r["title"], title_en=r.get("titleEn", ""),
                cuisine=r.get("cuisine", ""), meal_types=r.get("mealTypes", []),
                difficulty=r.get("difficulty", ""), complexity=r.get("complexity", ""),
                cook_time_min=r.get("cookTimeMin", 0),
                cooking_methods=r.get("cookingMethods", []), equipment=r.get("equipment", []),
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
