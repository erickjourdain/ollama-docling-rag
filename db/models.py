from datetime import datetime
from typing import Any, Optional
from sqlalchemy import CheckConstraint, String, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    """Modèle utilisateur pour gestion des utilisateurs"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String(25), default="USER")
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_active: Mapped[bool] = mapped_column(default=True)
 
class CollectionMetadata(Base):
    """Modèle collection pour gestion des métadonnées des collections"""
    __tablename__ = "collections_metadata"

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text,)
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

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    collection_id: Mapped[str] = mapped_column(Text, ForeignKey("collections_metadata.id"), nullable=False)
    inserted_by: Mapped[str] = mapped_column(Text, ForeignKey("users.id"), nullable=False)
    creator: Mapped[User] = relationship("User", lazy="joined")
    md5: Mapped[str] = mapped_column(Text)
    date_insertion: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False)

class Job(Base):
    """Modèle pour le stockage des jobs d'indexation des documents"""
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(default="queued")  
    progress: Mapped[str] = mapped_column(default="conversion")
    logs: Mapped[list] = mapped_column(JSON, default=list)
    type: Mapped[str] = mapped_column(Text)
    input_data: Mapped[str] = mapped_column(JSON)
    result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)