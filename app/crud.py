from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app import schemas, models
from app.utils.logger_config import logger


# ---------------------------
# Crear usuario
# ---------------------------
def create_user(db: Session, user: schemas.UserCreate):
    try:
        db_user = models.User(name=user.name, email=user.email)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"Usuario '{user.name}' creado correctamente con email '{user.email}'")
        return db_user

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al crear el usuario '{user.name}': {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error inesperado al crear el usuario '{user.name}': {e}")
        db.rollback()
        raise


# ---------------------------
# Obtener todos los usuarios
# ---------------------------
def get_users(db: Session):
    try:
        users = db.query(models.User).all()
        logger.info(f"Se obtuvieron {len(users)} usuarios de la base de datos")
        return users
    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al obtener usuarios: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al obtener usuarios: {e}")
        raise


# ---------------------------
# Buscar usuario por ID
# ---------------------------
def get_user_by_id(db: Session, user_id: int):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            logger.info(f"Usuario con ID {user_id} encontrado: {user.name}")
        else:
            logger.warning(f"No se encontró usuario con ID {user_id}")
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al buscar usuario por ID {user_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al buscar usuario por ID {user_id}: {e}")
        raise


# ---------------------------
# Buscar usuario por correo
# ---------------------------
def get_user_by_email(db: Session, email: str):
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        if user:
            logger.info(f"Usuario con email '{email}' encontrado: {user.name}")
        else:
            logger.warning(f"No se encontró usuario con email '{email}'")
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al buscar usuario por email '{email}': {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al buscar usuario por email '{email}': {e}")
        raise


# ---------------------------
# Actualizar usuario
# ---------------------------
def update_user(db: Session, db_user: models.User, user: schemas.UserCreate):
    try:
        db_user.name = user.name
        db_user.email = user.email
        db.commit()
        db.refresh(db_user)
        logger.info(f"Usuario ID {db_user.id} actualizado correctamente a '{user.name}' / '{user.email}'")
        return db_user
    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al actualizar usuario ID {db_user.id}: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error inesperado al actualizar usuario ID {db_user.id}: {e}")
        db.rollback()
        raise


# ---------------------------
# Eliminar usuario
# ---------------------------
def delete_user(db: Session, db_user: models.User):
    try:
        nombre = db_user.name
        db.delete(db_user)
        db.commit()
        logger.info(f"Usuario '{nombre}' eliminado correctamente de la base de datos")
    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al eliminar usuario '{db_user.name}': {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error inesperado al eliminar usuario '{db_user.name}': {e}")
        db.rollback()
        raise
