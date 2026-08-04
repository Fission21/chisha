import os
from pathlib import Path

# 数据目录：容器内为 /app/data/processed；本地仓库为 <repo>/data/processed
_CWD_DATA = Path("data/processed")
DATA_DIR = Path(
    os.environ.get("DATA_DIR")
    or (_CWD_DATA if _CWD_DATA.is_dir() else Path(__file__).resolve().parents[2] / "data" / "processed")
)
FOODS_FILE = DATA_DIR / "foods.json"
RECIPES_FILE = DATA_DIR / "recipes.json"

# 数据库：默认 SQLite（零配置、单文件）；如需 PostgreSQL 用环境变量覆盖 DATABASE_URL
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./var/chisha.db")