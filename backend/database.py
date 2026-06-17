from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://neondb_owner:npg_iChZM6j7WwEA@ep-royal-meadow-ao878lbx.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"sslmode": "require"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()