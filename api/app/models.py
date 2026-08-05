from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy import JSON
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
    meal_types = Column(JSON, default=list)
    difficulty = Column(String(16), default="")
    complexity = Column(String(8), default="")
    cooking_methods = Column(JSON, default=list)
    equipment = Column(JSON, default=list)
    cook_time_min = Column(Integer, default=0)
    servings = Column(Integer, default=1)
    summary = Column(Text, default="")
    cover_emoji = Column(String(16), default="")
    source_name = Column(String(128), default="本项目整理")
    source_url = Column(String(512), default="")
    source_license = Column(String(64), default="")
    source_revision = Column(String(128), default="")
    tags = Column(JSON, default=list)
    allergens = Column(JSON, default=list)
    tips = Column(JSON, default=list)
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

# ---------- 用户体系 ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    salt = Column(String(64))
    token = Column(String(64), index=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    profile = relationship("UserProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")
    diary = relationship("UserDiary", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    sex = Column(String(16), default="")
    age = Column(Integer, nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    body_fat = Column(Float, nullable=True)
    activity_level = Column(String(16), default="moderate")
    goal = Column(String(16), default="maintain")
    allergies = Column(JSON, default=list)
    preferred_cuisines = Column(JSON, default=list)
    user = relationship("User", back_populates="profile")

class UserFavorite(Base):
    __tablename__ = "user_favorites"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(String(64))
    __table_args__ = (UniqueConstraint("user_id", "recipe_id", name="uq_user_fav"),)
    user = relationship("User", back_populates="favorites")

class UserDiary(Base):
    __tablename__ = "user_diary"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String(16))
    items = Column(JSON, default=list)
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_diary"),)
    user = relationship("User", back_populates="diary")
