from typing import Optional

from jose import jwt
from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import RAGException
from db.models import User
from repositories import user_repository
from schemas import UserCreate, UserFilters, UsersListResponse, UserUpdate


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
        return user_repository.list_users(
            session=session,
            filters=filters
        )

    @staticmethod
    def create_user(
        session: Session,
        user: UserCreate,
        is_active: Optional[bool] = True
    ) -> User | None:
        """Création d'un utilisateur

        Args:
            session (Session): session d'accès à la base de données
            user (UserCreate): données pour la création de l'utilisateur
            is_active (Optional[bool], optional): activiation du compte. Defaults to True.

        Returns:
            User | None: utilisateur nouvellement créé
        """
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
    
    @staticmethod
    def update_user(
        session: Session,
        user_id: str,
        user: UserUpdate,
        current_user: User
    ) -> User | None:
        """Mise à jour des données d'un utilisateur

        Args:
            session (Session): session d'accès à la base de données
            user (UserUpdate): données de l'utilisateur à mettre à jour

        Returns:
            User | None: utilisateur mis à jour
        """
        if current_user.role != "ADMIN":
            if current_user.id != user_id:
                raise RAGException(
                    message="Opération interdite",
                    detail="Vous ne disposez pas des droits pour modifier un utilisateur"
                )
            if user.role is not None:
                raise RAGException(
                    message="Opération interdite",
                    detail="Vous ne disposez pas des droits pour modifier le rôle d'un utilisateur"
                )
            if user.is_activate is not None:
                raise RAGException(
                    message="Opération interdite",
                    detail="Vous ne disposez pas des droits pour modifier le statut d'un utilisateur"
                )
        if (user.password is not None and user.old_password is None):
            raise RAGException(
                message="Mot de passe manquant",
                detail="L'ancien mot de passe est nécessaire pour changer le mot de passe"
            )
        return user_repository.update_user(
            session=session,
            user=user,
            user_id=user_id
        )

    @staticmethod
    def blacklist_token(
        session: Session,
        token: str
    ) -> None:
        """Ajouter un token à la blacklist pour l'invalider

        Args:
            session (Session): session d'accès à la base de données
            token (str): token à blacklister
        """
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti is not None and exp is not None:
             user_repository.blacklist_token(
                session=session,
                jti=jti,
                exp=exp
            )
             
    @staticmethod
    def is_blacklisted_token(
        session: Session,
        jti: str
    ) -> bool:
        """Vérifier si un token est blacklister

        Args:
            session (Session): session d'accès à la base de données
            jti (str): identifiant du token à vérifier

        Returns:
            bool: True si le token est blacklister, False sinon
        """
        return user_repository.is_blacklisted_token(
            session=session,
            jti=jti
        )