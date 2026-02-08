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
        return user_repository.get_user(session=session, user_id=user_id)

    @staticmethod
    def create_user(
        session: Session,
        user: UserCreate
    ) -> User | None:
        db_user = user_repository.create_user(
            session=session,
            username=user.username,
            email=user.email,
            password=user.password,
            role= user.role
        )
        return db_user
    
    @staticmethod
    def create_first_admin(
        session: Session
    ) -> User | None:
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
        db_user = user_repository.get_user_by_name(
            session=session, 
            username=username
        )
        return db_user