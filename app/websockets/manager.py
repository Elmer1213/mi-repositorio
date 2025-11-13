from typing import Dict
from fastapi import WebSocket
import asyncio
import json
from app.utils.logger_config import logger


class WebSocketManager:
    def __init__(self):
        
        #--------------------------------------------------------
        # Diccionario de conexion activas: {client_id: websocket}
        #--------------------------------------------------------
        self.active_connections: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str):
        
        """Acepta y registra una nueva conexión WebSocket"""
        
        await websocket.accept()
        async with self.lock:
            self.active_connections[client_id] = websocket
        logger.info(f"webSocket conectado: {client_id} | Total: {len(self.active_connections)}")
        
        #--------------------------------
        # Enviar confirmación de conexión
        #--------------------------------
        await self.send_personal_message(
            {
                "type": "connected",
                "client_id": client_id,
                "message": "Conexión establecida"
            },
            client_id
        )
        
    def disconnect(self, client_id: str):
        """Eliminar la conexión cuando un cliente se desconecta."""
        
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f" Cliente desconectado: {client_id} | Total: {len(self.active_connections)}")
            
            

    async def send_personal_message(self, message: dict, client_id: str):
        
        """Enviar un mensaje a un cliente específico."""
        
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error al enviar mensaje a {client_id}: {str(e)}")
                self.disconnect(client_id)

    async def broadcast(self, message: str):
        
        """Enviar un mensaje a todos los clientes conectados."""
        
        if not self.active_connections:
            logger.debug("No hay conexiones WebSocket activas")
            return
        
        disconnected_clients=[]
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
                logger.debug(f"Error de broadcast a {client_id}: {message.get('percentage', 'N/A')}%")
            except Exception as e:
                logger.error(f"Error en broadcast a {client_id}: {str(e)}")
                disconnected_clients.append(client_id)
                
        #-------------------------------
        # Limpiar conexiones fallidas
        #------------------------------
        for client_id in  disconnected_clients:
            self.disconnect(client_id)
            
    async def disconnect_all(self):
        
        """Desconecta todos los clientes (Útil al cerrar la aplicación)"""
        
        for client_id in list(self.active_connections.keys()):
            try:
                websocket = self.active_connections[client_id]
                await websocket.close()
            except Exception as e:
                logger.error(f"Error al cerrar conexión {client_id}: {str(e)}")
            finally:
                self.disconnect(client_id)
                
        logger.info("Todas las conexiones WebSocket cerradas")
        
    def get_connection_count(self) -> int:
        
        """Devuelve el número de conexion activas"""
        
        return len(self.active_connections)
    

        
        