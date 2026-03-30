from fastapi import Request

from services import UserWebSocketManager

def get_user_ws_manager(request: Request) -> UserWebSocketManager:
    return request.app.state.user_ws_manager