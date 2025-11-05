import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Base para modelos
Base = declarative_base()

# URL de la base de datos desde variable de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

# Crear motor de conexión
engine = create_engine(DATABASE_URL, echo=True)  

# Crear sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
