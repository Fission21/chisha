from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db import Base

class Food(Base):
    __tablename__ = "foods"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), default="")
    name = Column(String(128), index=True)
    source = Column(String(64), default="")
    edible = Column(Float, default=100.0)
    energy_kcal = Column(Float, default=0.0)
    protein = Column(Float, default=0.0)
    fat = Column(Float, default=0.0)
    carbohydrate = Column(Float, default=0.0)
    dietary_fiber = Column(Float, default=0.0)
    cholesterol = Column(Float, default=0.0)
    vitamin_a = Column(Float, default=0.0)
    vitamin_c = Column(Float, default=0.0)
    vitamin_e = Column(Float, default=0.0)
    calcium = Column(Float, default=0.0)
    phosphorus = Column(Float, default=0.0)
    potassium = Column(Float, default=0.0)
    sodium = Column(Float, default=0.0)
    magnesium = Column(Float, default=0.0)
    iron = Column(Float, default=0.0)
    zinc = Column(Float, default=0.0)
    selenium = Column(Float, default=0.0)

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(String(64), primary_key=True)
    title = Column(String(128))
    title_en = Column(String(128), default="")
    cuisine = Column(String(32), default="")
    meal_types = Column(JSONB, default=list)
    difficulty = Column(String(16), default="")
    cook_time_min = Column(Integer, default=0)
    servings = Column(Integer, default=1)
    summary = Column(Text, default="")
    cover_emoji = Column(String(16), default="")
    tags = Column(JSONB, default=list)
    allergens = Column(JSONB, default=list)
    tips = Column(JSONB, default=list)
    energy_kcal = Column(Float, default=0.0)
    protein = Column(Float, default=0.0)
    fat = Column(Float, default=0.0)
    carbohydrate = Column(Float, default=0.0)
    dietary_fiber = Column(Float, default=0.0)
    sodium = Column(Float, default=0.0)
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    steps = relationship("RecipeStep", back_populates="recipe", cascade="all, delete-orphan", order_by="RecipeStep.step_order")

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(String(64), ForeignKey("recipes.id"))
    name = Column(String(128))
    unit = Column(String(16), default="g")
    amount = Column(Float, default=0.0)
    note = Column(String(128), default="")
    food_name = Column(String(128), default="")
    food_source = Column(String(64), default="")
    food_code = Column(String(32), default="")
    recipe = relationship("Recipe", back_populates="ingredients")

class RecipeStep(Base):
    __tablename__ = "recipe_steps"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(String(64), ForeignKey("recipes.id"))
    step_order = Column(Integer, default=0)
    text = Column(Text)
    duration_min = Column(Integer, nullable=True)
    heat = Column(String(32), nullable=True)
    recipe = relationship("Recipe", back_populates="steps")
