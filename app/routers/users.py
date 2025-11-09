from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db
from app.utils.logger_config import logger

router = APIRouter(prefix="/users", tags=["Users"])


# ---------------------------
# GET - Obtener todos los usuarios
# ---------------------------
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


# ---------------------------
# POST - Crear usuario
# ---------------------------
@router.post("/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Validar si ya existe el correo
        existing_user = crud.get_user_by_email(db, user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="El correo ya está registrado")

        db_user = crud.create_user(db, user)
        logger.info(f"Usuario '{user.name}' creado correctamente con email '{user.email}'")
        return db_user

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al crear usuario '{user.name}': {e}")
        raise HTTPException(status_code=500, detail="Error al crear usuario")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado al crear usuario '{user.name}': {e}")
        raise HTTPException(status_code=500, detail="Error al crear usuario")


# ---------------------------
# PUT - Actualizar usuario por ID
# ---------------------------
@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = crud.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Validar que el correo no pertenezca a otro usuario
        existing_user = crud.get_user_by_email(db, user.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="El correo ya pertenece a otro usuario")

        updated_user = crud.update_user(db, db_user, user)
        logger.info(f"Usuario ID {user_id} actualizado correctamente")
        return updated_user

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al actualizar usuario {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar usuario")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado al actualizar usuario {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar usuario")


# ---------------------------
# DELETE - Eliminar usuario por ID
# ---------------------------
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        db_user = crud.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        crud.delete_user(db, db_user)
        logger.info(f"Usuario ID {user_id} eliminado correctamente")
        return {"message": f"Usuario con ID {user_id} eliminado correctamente"}

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al eliminar usuario {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar usuario")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado al eliminar usuario {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar usuario")