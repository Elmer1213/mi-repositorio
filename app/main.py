from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.websockets.manager import WebSocketManager

from app.database import engine, Base
from app.models import User, ExcelUploadLog 
from app.routers import users, health, users_fake, excel_upload  
from app.utils.logger_config import logger

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI + MySQL (WSL)")

# CORS
origins = [
    "http://localhost:4200", 
    "http://frontend:4200",   
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

websocket_manager = WebSocketManager()

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Mantiene conexión abierta
    except Exception:
        websocket_manager.disconnect(websocket)


# Routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(users_fake.router)
app.include_router(excel_upload.router)  

# Manejo global de errores
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