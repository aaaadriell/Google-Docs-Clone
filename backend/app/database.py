from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
import os
from dotenv import load_dotenv
from fastapi import Depends
from typing import Annotated

load_dotenv()  # Load environment variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL")
# print(f"Database URL: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_session = Annotated[Session, Depends(get_db)]