from datetime import datetime, timedelta
import uuid
from typing import Optional
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from core import security
from core.config import settings
from db.models import TokenBlacklist, User
from schemas import UserFilters, UsersListResponse, UserOut
from schemas.user import UserUpdate


def create_user(
    session: Session,
    username: str,
    email: str,
    password: str,
    role: Optional[str],
    is_active: Optional[bool] = True
) -> User:
    """Création d'un utilisateur dans la base de données

    Args:
        session (Session): session d'accès à la base de données
        username (str): nom de l'utilisateur
        email (str): email de l'utilisateur
        password (str): mot de passe de l'utilisateur
        role (Optional[str]): role attribué à l'utilisateur
        is_active (Optional[bool]): statut d'activation de l'utilisateur

    Returns:
        User: utilisateur enregistré dans la base de données
    """
    db_user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        hashed_password = security.get_password_hash(password=password)
    )
    if role is not None:
        db_user.role=role
    if is_active is not None:
        db_user.is_active=is_active
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def list_users(
    session: Session,
    filters: UserFilters
) -> UsersListResponse:
    """Récupération de la liste des utilisateurs

    Args:
        session (Session): session d'accès à la base de données
        filters (UserFilters): filtres de recherche des utilisateurs

    Returns:
        UsersListResponse: liste des utilisateurs et leur nombre total
    """
    stmt = (
        select(User)
        .order_by(User.id)
        .limit(filters.limit)
        .offset(filters.offset)
    )
    stmt_count = select(func.count(User.id))
    if filters.search:
        stmt.where(or_(
            User.username.ilike(f"%{filters.search}%"),
            User.email.ilike(f"%{filters.search}%")
        ))
        stmt_count.where(or_(
            User.username.ilike(f"%{filters.search}%"),
            User.email.ilike(f"%{filters.search}%")
        ))
    if filters.is_active:
        stmt.where(User.is_active == filters.is_active)
        stmt_count.where(User.is_active == filters.is_active)
    result = session.execute(stmt)
    result_count = session.execute(stmt_count).scalar_one()
    return UsersListResponse(
        data=[UserOut.model_validate(u) for u in result.scalars().all()],
        count=result_count
    )

def get_user(
    session: Session,
    user_id: str
) -> User | None:
    """Récupération d'un utilisateur via son id

    Args:
        session (Session): session d'accès à la base de données
        user_id (str): id de l'utilisateur

    Returns:
        User | None: utilisateur enregistré dans la base
    """
    stmt = select(User).where(User.id == user_id)
    user = session.execute(stmt)
    return user.scalar_one_or_none()

def nb_users(
    session: Session
) -> int:
    """Nombre d'utilisateurs enregistrés dans la base

    Args:
        session (Session): session d'accès à la base de données

    Returns:
        int: nombre d'utilisateurs enregistrés
    """
    stmt = select(func.count()).select_from(User)
    nb_users = session.execute(stmt)
    return nb_users.scalar() or 0

def get_user_by_name(
    session: Session,
    username: str
) -> User | None:
    """Récupéraion d'un utilisateur via son nom

    Args:
        session (Session): session d'accès à la base de données
        username (str): nom de l'utilisateur recherché

    Returns:
        User | None: utilisateur enregistré dans la base
    """
    stmt = select(User).where(User.username == username)
    user = session.execute(stmt)
    return user.scalar_one_or_none()

def get_user_by_email(
    session: Session,
    email: str
) -> User | None:
    """Récupéraion d'un utilisateur via son email

    Args:
        session (Session): session d'accès à la base de données
        email (str): email de l'utilisateur recherché

    Returns:
        User | None: utilisateur enregistré dans la base
    """
    stmt = select(User).where(User.email == email)
    user = session.execute(stmt)
    return user.scalar_one_or_none()

def activate_user(
    session: Session,
    user_id: str
) -> User | None:
    """Activation d'un utilisateur

    Args:
        session (Session): session d'accès à la base de données
        user_id (str): id de l'utilisateur à activer

    Returns:
        User | None: utilisateur activé
    """
    user = get_user(session=session, user_id=user_id)
    if user is not None:
        user.is_active = True
        session.commit()
        session.refresh(user)
    return user

def update_user(
    session: Session,
    user: UserUpdate,
    user_id: str
) -> User | None:
    """Mise à jour des données d'un utilisateur dans la base de données

    Args:
        session (Session): sessions d'accès à la base de données
        user (UserUpdate): données de l'utilisateur
        user_id (str): identifiant de l'utilisateur

    Returns:
        User | None: utilisateur mis à jour
    """
    updated_user = get_user(session=session, user_id=user_id)
    if updated_user is not None:
        updated_user.username = (user.username) if user.username is not None else updated_user.username
        updated_user.role = (user.role) if user.role is not None else updated_user.role
        updated_user.email = (user.email) if user.email is not None else updated_user.email
        updated_user.username = (user.username) if user.username is not None else updated_user.username
        updated_user.is_active = (user.is_activate) if user.is_activate is not None else updated_user.is_active
        if user.password and user.old_password:
            if security.verify_password(
                plain_password=user.old_password, 
                hashed_password=updated_user.hashed_password
            ):
                updated_user.hashed_password=security.get_password_hash(
                    password=user.password
                )
            else:
                raise Exception("Mot de passe incorrect")
        session.commit()
        session.refresh(update_user)
    return updated_user

def is_blacklisted_token(
    session: Session,
    jti: str
) -> bool:
    """Vérification si un token est blacklisé

    Args:
        session (Session): session d'accès à la base de données
        jti (str): jti du token à vérifier

    Returns:
        bool: True si le token est blacklisé, False sinon
    """
    stmt = select(TokenBlacklist).where(TokenBlacklist.jti == jti)
    blacklisted_token = session.execute(stmt)
    return blacklisted_token.scalar_one_or_none() is not None

def blacklist_token(
    session: Session,
    jti: str,
    exp: int
) -> None:
    """Ajout d'un token à la blacklist pour l'invalider

    Args:
        session (Session): session d'accès à la base de données
        jti (str): jti du token d'accès à invalider
        exp (int): timestamp d'expiration du token
    """
    blacklisted_token = TokenBlacklist(
        id=str(uuid.uuid4()),
        jti=jti,
        expires_at=datetime.fromtimestamp(exp)
    )
    session.add(blacklisted_token)
    session.commit()

def cleanup_blacklisted_tokens(
    session: Session
) -> int:
    """Nettoyage des tokens blacklistés expirés

    Args:
        session (Session): session d'accès à la base de données

    Returns:
        int: nombre de tokens supprimés
    """
    stmt = select(TokenBlacklist).where(
        TokenBlacklist.blacklisted_at < datetime.now()+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    expired_tokens = session.execute(stmt).scalars().all()
    count = len(expired_tokens)
    for token in expired_tokens:
        session.delete(token)
    session.commit()
    return count