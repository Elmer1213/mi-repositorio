from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db
from app.utils.logger_config import logger 
from typing import List


router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    try:
        users = crud.get_users(db)
        logger.info(f"Se obtuvieron {len(users)} usuarios")
        return users
    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al obtener usuarios: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener usuarios")
    except Exception as e:
        logger.error(f"Error inesperado al obtener usuarios: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener usuarios")

@router.post("/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = crud.create_user(db, user)
        logger.info(f"Usuario '{user.name}' creado correctamente con email '{user.email}'")
        return db_user
    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al crear usuario '{user.name}': {e}")
        raise HTTPException(status_code=500, detail="Error al crear usuario")
    except Exception as e:
        logger.error(f"Error inesperado al crear usuario '{user.name}': {e}")
        raise HTTPException(status_code=500, detail="Error al crear usuario")
