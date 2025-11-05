from sqlalchemy.orm import Session
from app import schemas, models
from app.utils.logger_config import logger

def create_user(db: Session, user: schemas.UserCreate):
    try:
        db_user = models.User(name=user.name, email=user.email)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Registrar el evento en logs
        logger.info(f"Usuario '{user.name}' creado correctamente con email '{user.email}'")

        return db_user
    except Exception as e:
        # Registrar el error en logs
        logger.error(f"Error al crear el usuario '{user.name}': {e}")
        # Propagar el error para que FastAPI lo maneje
        raise

def get_users(db: Session):
    try:
        users = db.query(models.User).all()
        logger.info(f"Se obtuvieron {len(users)} usuarios de la base de datos")
        return users
    except Exception as e:
        logger.error(f"Error al obtener usuarios: {e}")
        raise
