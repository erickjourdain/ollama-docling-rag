from datetime import datetime, timedelta
import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any, Union
from fastapi import HTTPException, UploadFile, status
import filetype
from jose import jwt
from passlib.context import CryptContext
from pypdf import PdfReader

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: Union[str, Any]) -> str:
    """Création du jetond'accès à l'application

    Args:
        subject (Union[str, Any]): identifiant de l'utilisateur (généralement son ID ou son email)

    Returns:
        str: jeton d'accès encodé
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_password_hash(password: str) -> str:
    """Retourne le hash d'un mot de passe

    Args:
        password (str): mot de passe en clair à hasher

    Returns:
        str: hash du mot de passe
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérification d'un mot de passe par rapport à son hash

    Args:
        plain_password (str): mot de passe en clair à vérifier
        hashed_password (str): hash du mot de passe à comparer

    Returns:
        bool: True si le mot de passe correspond au hash, False sinon
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def hash_file(file_path: Path, chunk_size: int=4096):
    """Création du hash d'un fichier

    Args:
        file_path (Path): chemin du fichier à hasher
        chunk_size (int, optional): taille des morceaux de lecture. Defaults to 4096.

    Returns:
        str: hash MD5 du fichier
    """
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    return md5.hexdigest()

def verify_md5(file_path: Path, expected_hash: str, chunk_size: int=4096):
    """Vérification du hash d'un fichier par rapport à un hash attendu

    Args:
        file_path (Path): chemin du fichier à vérifier
        expected_hash (str): hash MD5 attendu pour le fichier
        chunk_size (int, optional): taille des morceaux de lecture. Defaults to 4096.

    Returns:
        bool: True si le hash du fichier correspond à expected_hash, False sinon
    """
    calculated_hash = hash_file(file_path, chunk_size)
    # Case-insensitive comparison is often needed
    return calculated_hash.lower() == expected_hash.lower()


async def validate_pdf(file: UploadFile):
    """Validation stricte d'un fichier PDF uploadé pour éviter les risques de sécurité liés à des fichiers malveillants.

    Args:
        file (UploadFile): Le fichier uploadé à valider.

    Raises:
        HTTPException: Aucun fichier sélectionné.
        HTTPException: Seuls les fichiers PDF sont acceptés.
        HTTPException: Impossible de déterminer le type de fichier.
        HTTPException: Fichier invalide.
        HTTPException: PDF protégé par mot de passe.
        HTTPException: PDF corrompu ou illisible.
    """
    # 1. Vérification que le fichier n'est pas vide
    if file.filename is None or file.filename.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun fichier sélectionné."
        )

    # 2. Vérification par extension (premier rempart)
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les fichiers PDF sont acceptés."
        )

    # 3. Vérification du contenu réel (Magic Numbers)
    # On lit le début du fichier
    head = await file.read(2048)
    await file.seek(0) # On remet TOUJOURS le curseur au début
    
    kind = filetype.guess(head)
    
    if kind is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de déterminer le type de fichier."
        )
    
    if kind.mime != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fichier invalide. Type détecté : {kind.mime} au lieu de application/pdf."
        )

    # 4. Vérification du Mot de Passe (Chiffrement)
    # On lit le fichier en mémoire pour pypdf (seulement les métadonnées)
    content = await file.read()
    await file.seek(0) # Toujours remettre au début !
    
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce PDF est protégé par un mot de passe et ne peut pas être traité."
            )
    except Exception:
        # Si pypdf n'arrive même pas à lire la structure, le PDF est corrompu
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier PDF semble corrompu ou illisible."
        )