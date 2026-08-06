# 种子数据：将 processed JSON 幂等地同步到数据库；用户数据表不受影响。
import json
from sqlalchemy import inspect, text
from app.db import Base, engine, SessionLocal
from app import models
from app.config import FOODS_FILE, RECIPES_FILE
from app.default_account import ensure_configured_default_account


RECIPE_METADATA_COLUMNS = {
    "cooking_methods": "JSON",
    "equipment": "JSON",
    "complexity": "VARCHAR(8) DEFAULT ''",
    "source_name": "VARCHAR(128) DEFAULT '本项目整理'",
    "source_url": "VARCHAR(512) DEFAULT ''",
    "source_license": "VARCHAR(64) DEFAULT ''",
    "source_revision": "VARCHAR(128) DEFAULT ''",
    "health_profile": "JSON",
}
USER_PROFILE_COLUMNS = {
    "health_profile": "VARCHAR(16) DEFAULT 'balanced'",
}


def ensure_recipe_metadata_columns():
    columns = {column["name"] for column in inspect(engine).get_columns("recipes")}
    missing = set(RECIPE_METADATA_COLUMNS) - columns
    if not missing:
        return
    with engine.begin() as conn:
        for name in sorted(missing):
            conn.execute(text(f"ALTER TABLE recipes ADD COLUMN {name} {RECIPE_METADATA_COLUMNS[name]}"))


def ensure_user_profile_columns():
    columns = {column["name"] for column in inspect(engine).get_columns("user_profiles")}
    missing = set(USER_PROFILE_COLUMNS) - columns
    if not missing:
        return
    with engine.begin() as conn:
        for name in sorted(missing):
            conn.execute(text(f"ALTER TABLE user_profiles ADD COLUMN {name} {USER_PROFILE_COLUMNS[name]}"))


def food_values(record):
    return {
        "code": record.get("code", ""), "name": record.get("name", ""), "source": record.get("source", ""),
        "edible": record.get("edible", 100.0),
        "energy_kcal": record.get("energyKCal", 0), "protein": record.get("protein", 0),
        "fat": record.get("fat", 0), "carbohydrate": record.get("CHO", 0),
        "dietary_fiber": record.get("dietaryFiber", 0), "cholesterol": record.get("cholesterol", 0),
        "vitamin_a": record.get("vitaminA", 0), "vitamin_c": record.get("vitaminC", 0),
        "vitamin_e": record.get("vitaminE", 0), "calcium": record.get("Ca", 0),
        "phosphorus": record.get("P", 0), "potassium": record.get("K", 0), "sodium": record.get("sodium", 0),
        "magnesium": record.get("Mg", 0), "iron": record.get("Fe", 0), "zinc": record.get("Zn", 0),
        "selenium": record.get("Se", 0),
    }


def recipe_values(record):
    nutrition = record.get("nutrition", {})
    source = record.get("source", {})
    return {
        "title": record["title"], "title_en": record.get("titleEn", ""),
        "cuisine": record.get("cuisine", ""), "meal_types": record.get("mealTypes", []),
        "difficulty": record.get("difficulty", ""), "complexity": record.get("complexity", ""),
        "cook_time_min": record.get("cookTimeMin", 0),
        "cooking_methods": record.get("cookingMethods", []), "equipment": record.get("equipment", []),
        "servings": record.get("servings", 1), "summary": record.get("summary", ""),
        "cover_emoji": record.get("coverEmoji", ""), "tags": record.get("tags", []),
        "allergens": record.get("allergens", []), "tips": record.get("tips", []),
        "health_profile": record.get("health", {}),
        "energy_kcal": nutrition.get("energyKCal", 0), "protein": nutrition.get("protein", 0),
        "fat": nutrition.get("fat", 0), "carbohydrate": nutrition.get("CHO", 0),
        "dietary_fiber": nutrition.get("dietaryFiber", 0), "sodium": nutrition.get("sodium", 0),
        "source_name": source.get("name", "本项目整理"), "source_url": source.get("url", ""),
        "source_license": source.get("license", ""), "source_revision": source.get("revision", ""),
    }


def sync_recipe(db, record, row=None):
    row = row or models.Recipe(id=record["id"])
    for key, value in recipe_values(record).items():
        setattr(row, key, value)
    if row not in db:
        db.add(row)

    # 菜谱是构建产物，可安全刷新；收藏、日记等用户表只保存 recipe_id，不会被改写。
    row.ingredients.clear()
    row.steps.clear()
    for ingredient in record.get("ingredients", []):
        row.ingredients.append(models.RecipeIngredient(
            name=ingredient.get("name", ""), unit=ingredient.get("unit", "g"),
            amount=ingredient.get("amount", 0), note=ingredient.get("note", ""),
            food_name=ingredient.get("food", {}).get("name", ""),
            food_source=ingredient.get("food", {}).get("source", ""),
            food_code=ingredient.get("food", {}).get("code", ""),
        ))
    for index, step in enumerate(record.get("steps", []), start=1):
        row.steps.append(models.RecipeStep(
            step_order=index, text=step.get("text", ""), duration_min=step.get("durationMin"),
            heat=step.get("heat"),
        ))


def seed():
    Base.metadata.create_all(engine)
    ensure_recipe_metadata_columns()
    ensure_user_profile_columns()
    db = SessionLocal()
    try:
        foods = json.loads(FOODS_FILE.read_bytes().decode("utf-8-sig"))
        recipes = json.loads(RECIPES_FILE.read_bytes().decode("utf-8-sig"))

        existing_foods = {(row.code, row.name, row.source): row for row in db.query(models.Food).all()}
        added_foods = 0
        for record in foods:
            values = food_values(record)
            key = (values["code"], values["name"], values["source"])
            row = existing_foods.get(key)
            if row is None:
                db.add(models.Food(**values))
                added_foods += 1
            else:
                for name, value in values.items():
                    setattr(row, name, value)

        existing_recipes = {row.id: row for row in db.query(models.Recipe).all()}
        added_recipes = 0
        for record in recipes:
            row = existing_recipes.get(record["id"])
            if row is None:
                added_recipes += 1
            sync_recipe(db, record, row)

        default_account_created = ensure_configured_default_account(db)
        db.commit()
        if default_account_created:
            print("created configured default account")
        print(f"synced foods={len(foods)} (+{added_foods}) recipes={len(recipes)} (+{added_recipes})")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
