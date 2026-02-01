from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """Modèle utilisateur pour gestion des utilisateurs"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class CollectionMetadata(Base):
    """Modèle collection pour gestion des métadonnées des collections"""
    __tablename__ = "collections_metadata"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", lazy="joined")
    date_creation = Column(DateTime, server_default=func.now())

class DocumentMetadata(Base):
    """Modèle document pour gestion des métadonnées des documents"""
    __tablename__ = "documents_metadata"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    collection_id = Column(String, ForeignKey("collections_metadata.id"), nullable=False)
    inserted_by = Column(String, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", lazy="joined")
    date_insertion = Column(DateTime, server_default=func.now())
