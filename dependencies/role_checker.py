from fastapi import HTTPException, status, Depends

from core.logging import logger
from db.models import User
from dependencies.security import get_current_user

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            logger.warning(f"Tentative d'accès non autorisé: User {user.username} (Role: {user.role})")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas les permissions nécessaires pour accéder à cette ressource."
            )
        return user

# On définit des raccourcis pour plus de clarté
allow_admin = RoleChecker(["ADMIN"])
allow_any_user = RoleChecker(["ADMIN", "USER"])