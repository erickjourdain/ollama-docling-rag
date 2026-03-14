from fastapi import WebSocket
from typing import Dict, List


class JobWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(job_id, []).append(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket):
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def send_update(self, job_id: str, data: dict):
        if job_id not in self.active_connections:
            return

        for ws in self.active_connections[job_id]:
            await ws.send_json(data)