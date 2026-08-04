# 测试默认使用 SQLite 临时库，无需 PostgreSQL / Docker
import os
import tempfile
from pathlib import Path

if not os.environ.get("DATABASE_URL"):
    _tmp = os.path.join(tempfile.gettempdir(), "chisha-test.db")
    os.environ["DATABASE_URL"] = "sqlite:///" + _tmp.replace("\\", "/")
    if os.path.exists(_tmp):
        os.remove(_tmp)
if not os.environ.get("DATA_DIR"):
    os.environ["DATA_DIR"] = str(Path(__file__).resolve().parents[2] / "data" / "processed")

import pytest
from app.seed import seed


@pytest.fixture(scope="session", autouse=True)
def _seeded_db():
    seed()
    yield