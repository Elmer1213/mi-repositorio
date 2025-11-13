from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.websockets.manager import WebSocketManager
from app.database import engine, Base
from app.models import User, ExcelUploadLog
from app.routers import users, health, excel_upload
from app.utils.logger_config import logger

#---------------------------
# Crear tablas si no existen
#--------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestión de Usuarios - SENA",
    description="API para carga masiva de usuarios desde Excel",
    version="1.0.0"
)

# CORS
origins = [
    "http://localhost:4200",
    "http://frontend:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#------------------
# WebSocket Manager
#3-----------------
websocket_manager = WebSocketManager()

#------------------------------------------
#MPORTANTE: Inyectar en el estado de la app
#------------------------------------------
app.state.websocket_manager = websocket_manager


@app.websocket("/ws/progress")
async def websocket_progress_endpoint(websocket: WebSocket):
    
    """WebSocket para progreso de carga Excel"""
    
    client_id = str(id(websocket))
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Cliente {client_id} envió: {data}")
            
            if data == "ping":
                await websocket_manager.send_personal_message(
                    {"type": "pong"},
                    client_id
                )
    
    except WebSocketDisconnect:
        logger.info(f"Cliente {client_id} desconectado")
        websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Error en WebSocket {client_id}: {str(e)}")
        websocket_manager.disconnect(client_id)


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Aplicación FastAPI iniciada")
    logger.info(f"WebSocket Manager: {websocket_manager}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Cerrando aplicación...")
    await websocket_manager.disconnect_all()

#--------------------------
#         Routers
#-------------------------
app.include_router(health.router)
app.include_router(users.router)
app.include_router(excel_upload.router)


@app.get("/api/endpoints", tags=["System"])
async def list_endpoints():
    """Lista todos los endpoints disponibles"""
    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name
            })
    return {
        "total": len(routes),
        "endpoints": sorted(routes, key=lambda x: x["path"])
    }


@app.get("/api/system/logs", tags=["System"])
async def get_system_logs(lines: int = 50):
    """Obtiene las últimas N líneas de logs"""
    try:
        log_file = "logs/app.log"
        with open(log_file, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
        recent_logs = log_lines[-lines:]
        return {
            "total_lines": len(log_lines),
            "lines_returned": len(recent_logs),
            "logs": [line.strip() for line in recent_logs]
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo de logs no encontrado")

#------------------
# Manejo de errores
#-------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Error de validación en {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"error": "Datos inválidos", "details": exc.errors()}
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
    logger.error(f"Error inesperado en {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor"}
    )


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "API de Gestión de Usuarios - SENA",
        "version": "1.0.0",
        "status": "running",
        "websocket_connections": websocket_manager.get_connection_count()
    }