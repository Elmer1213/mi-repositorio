from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException

# Importar Base y engine para crear tablas
from app.database import engine, Base
from app.models import User  # Importar todos los modelos que tengas

# Importar routers y logger
from app.routers import users, health
from app.utils.logger_config import logger

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# Inicializar app
app = FastAPI(title="FastAPI + MySQL (WSL)")

# Routers
app.include_router(health.router)
app.include_router(users.router)

# -----------------------
# Manejo global de errores
# -----------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Error de validación en {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"error": "Datos inválidos enviados. Revise los campos."}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException en {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error inesperado en {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Ocurrió un error interno. Consulte los logs para más detalles."}
    )
