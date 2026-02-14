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