from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import func, or_, desc
from typing import List, Optional
from app import schemas, models
from app.utils.logger_config import logger


# ===================================
# FUNCIONES DE VALIDACIÓN
# ===================================

def _validate_db_session(db: Session) -> bool:
    """
    Valida que la sesión de base de datos sea válida.
    
    Args:
        db: Sesión de SQLAlchemy
        
    Returns:
        bool: True si es válida, False si no
    """
    if db is None:
        logger.error("Sesión de base de datos es None")
        return False
    
    if not isinstance(db, Session):
        logger.error(f"db debe ser Session, recibido: {type(db)}")
        return False
    
    try:
        # Verificar que la sesión esté activa
        db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Sesión de BD inválida o cerrada: {str(e)}")
        return False


def _validate_user_id(user_id: int) -> bool:
    """
    Valida que el user_id sea válido.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        bool: True si es válido, False si no
    """
    if user_id is None:
        logger.error("user_id no puede ser None")
        return False
    
    if not isinstance(user_id, int):
        logger.error(f"user_id debe ser int, recibido: {type(user_id)}")
        return False
    
    if user_id <= 0:
        logger.error(f"user_id debe ser > 0, recibido: {user_id}")
        return False
    
    return True


def _validate_email(email: str) -> bool:
    """
    Valida que el email sea válido.
    
    Args:
        email: Email a validar
        
    Returns:
        bool: True si es válido, False si no
    """
    if not email:
        logger.error("email no puede estar vacío")
        return False
    
    if not isinstance(email, str):
        logger.error(f"email debe ser string, recibido: {type(email)}")
        return False
    
    if len(email.strip()) == 0:
        logger.error("email no puede ser solo espacios")
        return False
    
    if "@" not in email or "." not in email:
        logger.error(f"email tiene formato inválido: {email}")
        return False
    
    if len(email) > 255:
        logger.error(f"email demasiado largo ({len(email)} caracteres)")
        return False
    
    return True


def _validate_user_data(user: schemas.UserCreate) -> bool:
    """
    Valida los datos del usuario.
    
    Args:
        user: Objeto UserCreate con datos del usuario
        
    Returns:
        bool: True si es válido, False si no
    """
    if not user:
        logger.error("user no puede ser None")
        return False
    
    if not isinstance(user, schemas.UserCreate):
        logger.error(f"user debe ser UserCreate, recibido: {type(user)}")
        return False
    
    # Validar nombre
    if not user.name or not user.name.strip():
        logger.error("nombre no puede estar vacío")
        return False
    
    if len(user.name.strip()) < 2:
        logger.error(f"nombre debe tener mínimo 2 caracteres: '{user.name}'")
        return False
    
    if len(user.name.strip()) > 100:
        logger.error(f"nombre demasiado largo ({len(user.name)} caracteres)")
        return False
    
    # Validar email
    if not _validate_email(user.email):
        return False
    
    return True


def _validate_pagination_params(skip: int, limit: int) -> bool:
    """
    Valida parámetros de paginación.
    
    Args:
        skip: Registros a saltar
        limit: Máximo de registros a retornar
        
    Returns:
        bool: True si son válidos, False si no
    """
    if skip < 0:
        logger.error(f"skip debe ser >= 0, recibido: {skip}")
        return False
    
    if limit <= 0:
        logger.error(f"limit debe ser > 0, recibido: {limit}")
        return False
    
    if limit > 10000:
        logger.error(f"limit no puede exceder 10000, recibido: {limit}")
        return False
    
    return True


# ===================================
# FUNCIONES CRUD MEJORADAS
# ===================================

def create_user(db: Session, user: schemas.UserCreate) -> Optional[models.User]:
    """
    Crea un nuevo usuario en la base de datos.
    
    Args:
        db: Sesión de base de datos
        user: Datos del usuario a crear
        
    Returns:
        models.User: Usuario creado, o None si falló
        
    Raises:
        SQLAlchemyError: Error de base de datos
        ValueError: Datos inválidos
    """
    try:
        # Validar sesión de BD
        if not _validate_db_session(db):
            logger.error("Sesión de BD inválida en create_user")
            raise ValueError("Sesión de base de datos inválida")
        
        # Validar datos del usuario
        if not _validate_user_data(user):
            logger.error(f"Datos de usuario inválidos: {user}")
            raise ValueError("Datos de usuario inválidos")
        
        # Verificar que el email no exista (doble verificación)
        try:
            existing = get_user_by_email(db, user.email)
            if existing:
                logger.warning(f"⚠️ Intento de crear usuario con email duplicado: {user.email}")
                raise ValueError(f"El email '{user.email}' ya está registrado")
        except ValueError:
            raise
        except Exception as check_error:
            logger.error(f"Error al verificar email duplicado: {str(check_error)}")
            raise
        
        # Crear usuario
        try:
            db_user = models.User(
                name=user.name.strip(),
                email=user.email.strip().lower()
            )
            
            if not db_user:
                logger.error("No se pudo crear instancia de User")
                raise ValueError("Error al crear instancia de usuario")
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Verificar que se asignó un ID
            if not db_user.id or db_user.id <= 0:
                logger.error("Usuario creado sin ID válido")
                db.rollback()
                raise ValueError("Error al generar ID de usuario")
            
            logger.info(f"Usuario '{user.name}' creado con ID {db_user.id} y email '{user.email}'")
            return db_user
        
        except IntegrityError as integrity_error:
            logger.error(f"Error de integridad al crear usuario '{user.name}': {str(integrity_error)}")
            db.rollback()
            raise ValueError("Error de integridad: posible email duplicado")
        
        except SQLAlchemyError as db_error:
            logger.error(f"Error de BD al crear usuario '{user.name}': {str(db_error)}")
            db.rollback()
            raise
        
        except Exception as create_error:
            logger.error(f"Error inesperado al crear usuario '{user.name}': {str(create_error)}")
            db.rollback()
            raise

    except ValueError:
        raise
    except SQLAlchemyError:
        raise
    except Exception as e:
        logger.error(f"Error crítico en create_user: {str(e)}", exc_info=True)
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Error en rollback: {str(rollback_error)}")
        raise


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """
    Obtiene una lista de usuarios con paginación.
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a saltar (default: 0)
        limit: Máximo de registros a retornar (default: 100)
        
    Returns:
        List[models.User]: Lista de usuarios
        
    Raises:
        SQLAlchemyError: Error de base de datos
        ValueError: Parámetros inválidos
    """
    try:
        # Validar sesión de BD
        if not _validate_db_session(db):
            logger.error("Sesión de BD inválida en get_users")
            raise ValueError("Sesión de base de datos inválida")
        
        # Validar parámetros de paginación
        if not _validate_pagination_params(skip, limit):
            logger.error(f"Parámetros de paginación inválidos: skip={skip}, limit={limit}")
            raise ValueError("Parámetros de paginación inválidos")
        
        # Obtener usuarios
        try:
            users = db.query(models.User).offset(skip).limit(limit).all()
            
            if users is None:
                logger.warning("Query retornó None en lugar de lista vacía")
                users = []
            
            logger.info(f"Se obtuvieron {len(users)} usuario(s) (skip={skip}, limit={limit})")
            return users
        
        except OperationalError as op_error:
            logger.error(f"Error operacional al obtener usuarios: {str(op_error)}")
            raise
        
        except SQLAlchemyError as db_error:
            logger.error(f"Error de BD al obtener usuarios: {str(db_error)}")
            raise
        
        except Exception as query_error:
            logger.error(f"Error en query de usuarios: {str(query_error)}")
            raise

    except ValueError:
        raise
    except SQLAlchemyError:
        raise
    except Exception as e:
        logger.error(f"Error crítico en get_users: {str(e)}", exc_info=True)
        raise


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """
    Busca un usuario por su ID.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario a buscar
        
    Returns:
        models.User: Usuario encontrado, o None si no existe
        
    Raises:
        SQLAlchemyError: Error de base de datos
        ValueError: Parámetros inválidos
    """
    try:
        # Validar sesión de BD
        if not _validate_db_session(db):
            logger.error("Sesión de BD inválida en get_user_by_id")
            raise ValueError("Sesión de base de datos inválida")
        
        # Validar user_id
        if not _validate_user_id(user_id):
            logger.error(f"user_id inválido: {user_id}")
            raise ValueError(f"user_id inválido: {user_id}")
        
        # Buscar usuario
        try:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            
            if user:
                logger.info(f"Usuario con ID {user_id} encontrado: {user.name} ({user.email})")
            else:
                logger.info(f"No se encontró usuario con ID {user_id}")
            
            return user
        
        except OperationalError as op_error:
            logger.error(f"Error operacional al buscar usuario {user_id}: {str(op_error)}")
            raise
        
        except SQLAlchemyError as db_error:
            logger.error(f"Error de BD al buscar usuario {user_id}: {str(db_error)}")
            raise
        
        except Exception as search_error:
            logger.error(f"Error al buscar usuario {user_id}: {str(search_error)}")
            raise

    except ValueError:
        raise
    except SQLAlchemyError:
        raise
    except Exception as e:
        logger.error(f"Error crítico en get_user_by_id: {str(e)}", exc_info=True)
        raise


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Busca un usuario por su email.
    
    Args:
        db: Sesión de base de datos
        email: Email del usuario a buscar
        
    Returns:
        models.User: Usuario encontrado, o None si no existe
        
    Raises:
        SQLAlchemyError: Error de base de datos
        ValueError: Parámetros inválidos
    """
    try:
        # Validar sesión de BD
        if not _validate_db_session(db):
            logger.error("Sesión de BD inválida en get_user_by_email")
            raise ValueError("Sesión de base de datos inválida")
        
        # Validar email
        if not _validate_email(email):
            logger.error(f"email inválido: {email}")
            raise ValueError(f"Email inválido: {email}")
        
        # Normalizar email (lowercase)
        normalized_email = email.strip().lower()
        
        # Buscar usuario
        try:
            user = db.query(models.User).filter(
                func.lower(models.User.email) == normalized_email
            ).first()
            
            if user:
                logger.info(f"Usuario con email '{email}' encontrado: {user.name} (ID {user.id})")
            else:
                logger.info(f"No se encontró usuario con email '{email}'")
            
            return user
        
        except OperationalError as op_error:
            logger.error(f"Error operacional al buscar por email '{email}': {str(op_error)}")
            raise
        
        except SQLAlchemyError as db_error:
            logger.error(f"Error de BD al buscar por email '{email}': {str(db_error)}")
            raise
        
        except Exception as search_error:
            logger.error(f"Error al buscar por email '{email}': {str(search_error)}")
            raise

    except ValueError:
        raise
    except SQLAlchemyError:
        raise
    except Exception as e:
        logger.error(f"Error crítico en get_user_by_email: {str(e)}", exc_info=True)
        raise


def update_user(db: Session, db_user: models.User, user: schemas.UserCreate) -> Optional[models.User]:
    """
    Actualiza un usuario existente.
    
    Args:
        db: Sesión de base de datos
        db_user: Usuario a actualizar (objeto de BD)
        user: Nuevos datos del usuario
        
    Returns:
        models.User: Usuario actualizado, o None si falló
        
    Raises:
        SQLAlchemyError: Error de base de datos
        ValueError: Datos inválidos
    """
    try:
        # Validar sesión de BD
        if not _validate_db_session(db):
            logger.error("Sesión de BD inválida en update_user")
            raise ValueError("Sesión de base de datos inválida")
        
        # Validar db_user
        if not db_user:
            logger.error("db_user no puede ser None")
            raise ValueError("Usuario a actualizar no proporcionado")
        
        if not isinstance(db_user, models.User):
            logger.error(f"db_user debe ser User, recibido: {type(db_user)}")
            raise ValueError("Usuario inválido")
        
        if not db_user.id or db_user.id <= 0:
            logger.error(f"db_user sin ID válido: {db_user.id}")
            raise ValueError("Usuario sin ID válido")
        
        # Validar nuevos datos
        if not _validate_user_data(user):
            logger.error(f"Datos de actualización inválidos para usuario {db_user.id}")
            raise ValueError("Datos de actualización inválidos")
        
        # Guardar datos originales para logging
        original_name = db_user.name
        original_email = db_user.email
        user_id = db_user.id
        
        # Verificar si el nuevo email ya existe (si cambió)
        new_email = user.email.strip().lower()
        if new_email != db_user.email.lower():
            try:
                existing = get_user_by_email(db, new_email)
                if existing and existing.id != user_id:
                    logger.warning(f"Email '{new_email}' ya pertenece a otro usuario (ID {existing.id})")
                    raise ValueError(f"El email '{user.email}' ya está en uso")
            except ValueError:
                raise
            except Exception as check_error:
                logger.error(f"Error al verificar email: {str(check_error)}")
                raise
        
        # Actualizar usuario
        try:
            db_user.name = user.name.strip()
            db_user.email = new_email
            
            db.commit()
            db.refresh(db_user)
            
            # Verificar que la actualización fue exitosa
            if not db_user:
                logger.error(f"Usuario {user_id} es None después de actualizar")
                db.rollback()
                raise ValueError("Error al actualizar usuario")
            
            logger.info(
                f"Usuario ID {user_id} actualizado | "
                f"Nombre: '{original_name}' → '{db_user.name}' | "
                f"Email: '{original_email}' → '{db_user.email}'"
            )
            return db_user
        
        except IntegrityError as integrity_error:
            logger.error(f"Error de integridad al actualizar usuario {user_id}: {str(integrity_error)}")
            db.rollback()
            raise ValueError("Error de integridad: posible email duplicado")
        
        except SQLAlchemyError as db_error:
            logger.error(f"Error de BD al actualizar usuario {user_id}: {str(db_error)}")
            db.rollback()
            raise
        
        except Exception as update_error:
            logger.error(f"Error al actualizar usuario {user_id}: {str(update_error)}")
            db.rollback()
            raise

    except ValueError:
        raise
    except SQLAlchemyError:
        raise
    except Exception as e:
        logger.error(f"Error crítico en update_user: {str(e)}", exc_info=True)
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Error en rollback: {str(rollback_error)}")
        raise


def delete_user(db: Session, db_user: models.User) -> bool:
    """
    Elimina un usuario de la base de datos.
    
    Args:
        db: Sesión de base de datos
        db_user: Usuario a eliminar
        
    Returns:
        bool: True si se eliminó correctamente, False si no
        
    Raises:
        SQLAlchemyError: Error de base de datos
        ValueError: Datos inválidos
    """
    try:
        # Validar sesión de BD
        if not _validate_db_session(db):
            logger.error("Sesión de BD inválida en delete_user")
            raise ValueError("Sesión de base de datos inválida")
        
        # Validar db_user
        if not db_user:
            logger.error("db_user no puede ser None")
            raise ValueError("Usuario a eliminar no proporcionado")
        
        if not isinstance(db_user, models.User):
            logger.error(f"db_user debe ser User, recibido: {type(db_user)}")
            raise ValueError("Usuario inválido")
        
        if not db_user.id or db_user.id <= 0:
            logger.error(f"db_user sin ID válido: {db_user.id}")
            raise ValueError("Usuario sin ID válido")
        
        # Guardar información para logging
        user_id = db_user.id
        user_name = db_user.name
        user_email = db_user.email
        
        # Eliminar usuario
        try:
            db.delete(db_user)
            db.commit()
            
            logger.info(f"Usuario eliminado | ID: {user_id} | Nombre: '{user_name}' | Email: '{user_email}'")
            return True
        
        except IntegrityError as integrity_error:
            logger.error(f"Error de integridad al eliminar usuario {user_id}: {str(integrity_error)}")
            db.rollback()
            raise ValueError("No se puede eliminar: el usuario tiene dependencias")
        
        except SQLAlchemyError as db_error:
            logger.error(f"Error de BD al eliminar usuario {user_id}: {str(db_error)}")
            db.rollback()
            raise
        
        except Exception as delete_error:
            logger.error(f"Error al eliminar usuario {user_id}: {str(delete_error)}")
            db.rollback()
            raise

    except ValueError:
        raise
    except SQLAlchemyError:
        raise
    except Exception as e:
        logger.error(f"Error crítico en delete_user: {str(e)}", exc_info=True)
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"❌ Error en rollback: {str(rollback_error)}")
        raise


# ===================================
# FUNCIONES ADICIONALES ÚTILES
# ===================================

def search_users(db: Session, query: str, skip: int = 0, limit: int = 100) -> List[models.User]:
    """
    Busca usuarios por nombre o email.
    
    Args:
        db: Sesión de base de datos
        query: Término de búsqueda
        skip: Registros a saltar
        limit: Máximo de registros
        
    Returns:
        List[models.User]: Lista de usuarios encontrados
    """
    try:
        # Validaciones
        if not _validate_db_session(db):
            raise ValueError("Sesión de base de datos inválida")
        
        if not query or not query.strip():
            logger.warning("Query de búsqueda vacío, retornando lista vacía")
            return []
        
        if not _validate_pagination_params(skip, limit):
            raise ValueError("Parámetros de paginación inválidos")
        
        # Normalizar búsqueda
        search_term = f"%{query.strip().lower()}%"
        
        # Buscar en nombre o email
        users = db.query(models.User).filter(
            or_(
                func.lower(models.User.name).like(search_term),
                func.lower(models.User.email).like(search_term)
            )
        ).offset(skip).limit(limit).all()
        
        if users is None:
            users = []
        
        logger.info(f"Búsqueda '{query}': {len(users)} resultado(s)")
        return users
    
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error en search_users: {str(e)}")
        raise


def count_users(db: Session) -> int:
    """
    Cuenta el total de usuarios en la base de datos.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        int: Número total de usuarios
    """
    try:
        if not _validate_db_session(db):
            raise ValueError("Sesión de base de datos inválida")
        
        count = db.query(func.count(models.User.id)).scalar()
        count = int(count) if count is not None else 0
        
        logger.info(f"Total de usuarios: {count}")
        return count
    
    except Exception as e:
        logger.error(f"Error en count_users: {str(e)}")
        raise


def get_latest_users(db: Session, limit: int = 10) -> List[models.User]:
    """
    Obtiene los usuarios más recientes.
    
    Args:
        db: Sesión de base de datos
        limit: Número de usuarios a retornar
        
    Returns:
        List[models.User]: Lista de usuarios más recientes
    """
    try:
        if not _validate_db_session(db):
            raise ValueError("Sesión de base de datos inválida")
        
        if limit <= 0 or limit > 1000:
            logger.warning(f"Limit inválido ({limit}), usando 10")
            limit = 10
        
        users = db.query(models.User).order_by(desc(models.User.id)).limit(limit).all()
        
        if users is None:
            users = []
        
        logger.info(f"Últimos {len(users)} usuario(s) obtenidos")
        return users
    
    except Exception as e:
        logger.error(f"Error en get_latest_users: {str(e)}")
        raise


def user_exists(db: Session, user_id: int) -> bool:
    """
    Verifica si un usuario existe por su ID.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario
        
    Returns:
        bool: True si existe, False si no
    """
    try:
        if not _validate_db_session(db):
            return False
        
        if not _validate_user_id(user_id):
            return False
        
        exists = db.query(models.User).filter(models.User.id == user_id).count() > 0
        return exists
    
    except Exception as e:
        logger.error(f"Error en user_exists: {str(e)}")
        return False


def email_exists(db: Session, email: str) -> bool:
    """
    Verifica si un email ya está registrado.
    
    Args:
        db: Sesión de base de datos
        email: Email a verificar
        
    Returns:
        bool: True si existe, False si no
    """
    try:
        if not _validate_db_session(db):
            return False
        
        if not _validate_email(email):
            return False
        
        normalized_email = email.strip().lower()
        exists = db.query(models.User).filter(
            func.lower(models.User.email) == normalized_email
        ).count() > 0
        
        return exists
    
    except Exception as e:
        logger.error(f"Error en email_exists: {str(e)}")
        return False