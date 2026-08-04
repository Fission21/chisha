from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL

# SQLite 是文件库：确保父目录存在，并允许跨线程使用（FastAPI 多线程）
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL[len("sqlite:///") :]
        if db_path and db_path != ":memory:":
            parent = Path(db_path).parent
            if str(parent) not in ("", "."):
                parent.mkdir(parents=True, exist_ok=True)
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()