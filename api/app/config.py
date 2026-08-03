import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/data/processed"))
FOODS_FILE = DATA_DIR / "foods.json"
RECIPES_FILE = DATA_DIR / "recipes.json"

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://chisha:chisha@localhost:5432/chisha",
)
