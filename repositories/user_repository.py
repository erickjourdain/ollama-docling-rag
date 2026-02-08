import uuid
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core import security
from db.models import User


def create_user(
    session: Session,
    username: str,
    email: str,
    password: str,
    role: Optional[str]
) -> User:
    """Création d'un utilisateur dans la base de données

    Args:
        session (Session): session d'accès à la base de données
        username (str): nom de l'utilisateur
        email (str): email de l'utilisateur
        password (str): mot de passe de l'utilisateur
        role (Optional[str]): role attribué à l'utilisateur

    Returns:
        User: utilisateur enregistré dans la base de données
    """
    db_user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        hashed_password = security.hash_password(password=password)
    )
    if role is not None:
        db_user.role=role
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

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
    stmt = select(User).where(User.username == username and User.is_active)
    user = session.execute(stmt)
    return user.scalar_one_or_none()