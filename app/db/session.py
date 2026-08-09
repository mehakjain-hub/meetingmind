"""
Reads DB connection details from .env (gitignored) so credentials never
hit version control, and so local vs. deployed (Supabase/Neon) connections
just mean swapping .env values, not touching code.
"""

import os
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "meetingmind")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

if not DB_USER:
    raise RuntimeError(
        f"DB_USER not set. Expected a .env file at {ENV_PATH} with DB_HOST, "
        f"DB_PORT, DB_NAME, DB_USER, DB_PASSWORD defined."
    )

"""
psycopg2 connection string. If DB_PASSWORD is empty (common for local
Postgres.app trust-auth setups), this still works correctly.
"""

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

"""
echo = False by default; flip to True temporarily if we need to see the raw
SQL SQLAlchemy is generating for debugging.
"""

_engine = create_engine(DATABASE_URL, echo = False, future = True)
_SessionLocal = sessionmaker(bind = _engine, autoflush = False)

Base = declarative_base()

def get_engine():
    return _engine

def get_session():
    return _SessionLocal()

@contextmanager
def session_scope():
    """
    Context manager that yields a session, commits on success, rolls back
    on exception, and always closes the session afterward.
    """
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    try:
        engine = get_engine()
        with engine.connect() as conn:
            print(f"Connected Successfully to database '{DB_NAME}' at {DB_HOST} : {DB_PORT}")
    except Exception as e:
        print(f"Connection failed: {e}")