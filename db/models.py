from datetime import datetime
from typing import Optional
from sqlalchemy import CheckConstraint, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship

from core.config import settings

class Base(DeclarativeBase):
    pass

class User(Base):
    """Modèle utilisateur pour gestion des utilisateurs"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String(25), default="USER")
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_active: Mapped[bool] = mapped_column(default=True)
 
class CollectionMetadata(Base):
    """Modèle collection pour gestion des métadonnées des collections"""
    __tablename__ = "collections_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(Text, ForeignKey("users.id"), nullable=False)
    creator: Mapped[User] = relationship("User", lazy="joined")
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (
            CheckConstraint(
                "length(name) >= 5 AND length(name) <= 25", 
                name="name_length_check"
            ),
            # SQLite supporte le filtrage par REGEXP si l'extension est chargée, 
            # sinon on utilise GLOB pour une vérification basique :
            CheckConstraint(
                "name NOT LIKE '% %'", # Pas d'espaces
                name="no_space_check"
            ),
        )

class DocumentMetadata(Base):
    """Modèle document pour gestion des métadonnées des documents"""
    __tablename__ = "documents_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    collection_id: Mapped[str] = mapped_column(String(36), ForeignKey("collections_metadata.id"), nullable=False)
    inserted_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    creator: Mapped[User] = relationship("User", lazy="joined")
    md5: Mapped[str] = mapped_column(Text)
    date_insertion: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False)

class Job(Base):
    """Modèle pour le stockage des jobs d'indexation des documents"""
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)

    type: Mapped[str] = mapped_column(String(55), nullable=False)
    status: Mapped[str] = mapped_column(String(25), default="pending")  
    progress: Mapped[str] = mapped_column(String(25), default="waiting")

    attemps: Mapped[int] = mapped_column(Integer, default=0)
    max_attemps: Mapped[int] = mapped_column(Integer, default=3)

    logs: Mapped[list] = mapped_column(JSON, default=list)
    error_message: Mapped[str] = mapped_column(String(255), default=None, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)

class TokenBlacklist(Base):
    """Modèle pour le stockage des tokens d'authentification invalidés (blacklist)"""
    __tablename__ = "token_blacklist"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    jti: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    blacklisted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class Query(Base):
    """Modèle pour le stockage des interrogations des base de connaissance"""
    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    user: Mapped[User] = relationship("User", lazy="joined")    
    inserted_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    collection: Mapped[CollectionMetadata] = relationship("CollectionMetadata", lazy="joined")
    collection_id: Mapped[str] = mapped_column(String(36), ForeignKey("collections_metadata.id"), nullable=False)
    job: Mapped[Job] = relationship("Job", lazy="joined")
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=False)

    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(125), default=settings.LLM_MODEL)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
