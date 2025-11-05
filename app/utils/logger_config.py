import os
import logging
from logging.handlers import RotatingFileHandler
import sys

# Crear carpeta logs si no existe
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("mi_proyecto_logger")
logger.setLevel(logging.INFO)

# Formatter común
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

#RotatingFileHandler para archivo
file_handler = RotatingFileHandler(
    "logs/app.log",
    maxBytes=5*1024*1024,
    backupCount=3,
    encoding="utf-8",
    delay=False
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

#StreamHandler para consola (ver en terminal en tiempo real)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Evitar múltiples handlers duplicados
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

#Forzar flush inmediato para RotatingFileHandler
file_handler.flush = file_handler.stream.flush
