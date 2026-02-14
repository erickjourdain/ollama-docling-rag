from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from core.logging import logger
from db.models import User
from dependencies.sqlite_session import get_db
from core.config import settings
from services.user_service import UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """Récupère l'utilisateur courant à partir du token d'authentification.

    Args:
        token (str, optional): token d'authentification JWT. Defaults to Depends(oauth2_scheme).
        db (Session, optional): session de base de données. Defaults to Depends(get_db).

    Raises:
        credentials_exception: Exception levée lorsque le token est invalide ou que l'utilisateur n'est pas trouvé
        credentials_exception: Exception levée lorsque le token est invalide ou que l'utilisateur n'est pas trouvé
        credentials_exception: Exception levée lorsque le token est invalide ou que l'utilisateur n'est pas trouvé

    Returns:
        User: utilisateur correspondant au token d'authentification
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        jti: str | None = payload.get("jti")
        if jti is None:
            raise credentials_exception
        is_blacklisted_token = UserService.is_blacklisted_token(
            session=db, 
            jti=jti
        )
        if is_blacklisted_token:
            logger.warning(f"Tentative de connexion avec un token blacklisé: {jti}")
            raise credentials_exception 
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user