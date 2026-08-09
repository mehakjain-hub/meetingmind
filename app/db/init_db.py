import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import get_engine, Base
from app.db import models  # noqa: F401 - import registers model classes on Base.metadata

Base.metadata.create_all(bind=get_engine())
print("Tables created.")