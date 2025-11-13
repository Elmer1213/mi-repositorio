"""
Script para inicializar la base de datos y crear las tablas
Ejecutar: python init_db.py
"""


from app.database import engine, Base
from app.models import User, ExcelUploadLog
from app.utils.logger_config import logger

def init_database():
    
    """Crea todas las tabals en al base de datos"""
    
    try:
        logger.info("Inicializando base de datos")
        
        #Crear todas la tablas
        Base.metadata.create_all(bind=engine)
        
        logger.info("Tablas creada exitosamente")
        logger.info(" - users")
        logger.info(" - excel_upload_logs")
        
        #verifica tablas creadas
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"Tablas en la base de datos: {tables}")
        
        return False
    
    except Exception as e:
        logger.error(f"Error al crear tablas: {str(e)}")
        return False
    
if __name__ == "__main__":
        success = init_database()
        
        if success:
            print("\nBase de datos inicializada correctamente")
            print("Puedes iniciar la aplicación con: uvicorn app.main:app --reload")
        else:
            print("\nError al inicializar la base de datos")
            print("Verifica tu configuración y la conexión a MySQL")
    
    
    