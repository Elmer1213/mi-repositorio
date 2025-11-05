# app/routers/health.py
from fastapi import APIRouter

router = APIRouter()  # Crea un grupo de rutas

@router.get("/health", tags=["Health"])
def health_check():
    """
    Endpoint simple para verificar el estado del servidor.
    """
    return {"status": "ok"}
