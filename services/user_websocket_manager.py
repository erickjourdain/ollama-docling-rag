from fastapi import WebSocket
from typing import Dict, List

from pydantic import BaseModel

class UserWebSocketManager:
    """Class de gestion des websockets
    """
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """Connexion d'un nouvel utilisateur

        Args:
            user_id (str): identifiant de l'utilisateur
            websocket (WebSocket): websocket
        """
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        """Déconnexion de l'utilisateur

        Args:
            user_id (str): identifiant de l'utilisateur
            websocket (WebSocket): websocket
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, data: BaseModel):
        """Envoi d'information à l'utilisateur

        Args:
            user_id (str): identifiant de l'utilisateur
            data (dict): information à envoyer sous forme de dictionnaire
        """
        if user_id not in self.active_connections:
            return

        for ws in self.active_connections[user_id]:
            await ws.send_json(data.model_dump(mode="json"))

    async def receive_text(self):
        """_summary_

        Args:
            message (str): _description_
        """
        return