from typing import Optional

from sqlalchemy.orm import Session

from core.config import settings
from db.models import User
from repositories import user_repository
from schemas import UserCreate


class UserService:

    @staticmethod
    def get_user(
        session: Session,
        user_id: str
    ) -> User | None:
        """Récupération d'un utilisateur via son identifiant

        Args:
            session (Session): session d'accès à la base de données
            user_id (str): identifiant de l'utilisateur

        Returns:
            User | None: utilisateur
        """
        return user_repository.get_user(session=session, user_id=user_id)

    @staticmethod
    def create_user(
        session: Session,
        user: UserCreate,
        is_active: Optional[bool] = True
    ) -> User | None:
        db_user = user_repository.create_user(
            session=session,
            username=user.username,
            email=user.email,
            password=user.password,
            role=user.role,
            is_active=is_active or False
        )
        return db_user
    
    @staticmethod
    def create_first_admin(
        session: Session
    ) -> User | None:
        """Créer le premier utilisateur en tant qu'administrateur de la base

        Args:
            session (Session): session d'accès à la base de données

        Returns:
            User | None: utilisateur créé
        """
        nb_users = user_repository.nb_users(session=session)
        if nb_users == 0:
            user = UserCreate(
                username=settings.FIRST_USER_USERNAME,
                password=settings.FIRST_USER_PWD,
                email=settings.FIRST_USER_EMAIL,
                role="ADMIN"
            )
            db_user = UserService.create_user(session=session, user=user)
            return db_user
        else:
            return None
    
    @staticmethod
    def get_user_by_name(
        session: Session,
        username: str
    ) -> User | None:
        """Récupération d'un utilisateur via son nom

        Args:
            session (Session): session d'accès à la base de données
            username (str): nom de l'utilisateur recherché

        Returns:
            User | None: utilisateur
        """
        db_user = user_repository.get_user_by_name(
            session=session, 
            username=username
        )
        return db_user
    
    @staticmethod
    def check_existing_user(
        session: Session,
        email: str,
        username: str
    ) -> User | None:
        """Récupération d'un utilisateur via son email ou son usernanme

        Args:
            session (Session): session d'accès à la base de données
            email (str): email de l'utilisateur recherché
            username (str): nom de l'utilisateur recherché

        Returns:
            User | None: utilisateur
        """
        db_user = user_repository.get_user_by_email(
            session=session, 
            email=email
        )
        if db_user is not None:
            return db_user
        db_user = user_repository.get_user_by_name(
            session=session, 
            username=username
        )
        return db_user
    
    @staticmethod
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
        db_user = user_repository.activate_user(
            session=session, 
            user_id=user_id
        )
        return db_user