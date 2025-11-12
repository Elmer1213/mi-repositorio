# app/websockets/manager.py

from typing import Dict
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Aceptar la conexión y guardarla."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Cliente conectado: {client_id}")

    def disconnect(self, client_id: str):
        """Eliminar la conexión cuando un cliente se desconecta."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f" Cliente desconectado: {client_id}")

    async def send_personal_message(self, message: str, client_id: str):
        """Enviar un mensaje a un cliente específico."""
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Enviar un mensaje a todos los clientes conectados."""
        for websocket in self.active_connections.values():
            await websocket.send_text(message)
