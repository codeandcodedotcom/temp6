from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from app.config import Config

_db_url = None
if getattr(Config, "DATABASE_URL", None):
    _db_url = Config.DATABASE_URL
else:
    # fall back to DB_PATH or sqlite in ./data/database.db
    db_path = None
    if getattr(Config, "DB_PATH", None):
        db_path = Config.DB_PATH
    else:
        db_path = "./backend/data/database.db"
    # create sqlite URL
    _db_url = f"sqlite:///{os.path.abspath(db_path)}"


_engine_args = {}
if _db_url.startswith("sqlite:///"):
    # For SQLite in multi-threaded app, allow check_same_thread=False if using sessions across threads.
    _engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(_db_url, pool_pre_ping=True, **_engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()

def get_db_session():
    return SessionLocal()
