from datetime import datetime, timedelta
import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any, Union
import uuid
import bcrypt
from fastapi import HTTPException, UploadFile, status
import filetype
from jose import jwt
from pypdf import PdfReader

from .config import settings



def create_access_token(subject: Union[str, Any]) -> str:
    """Création du jetond'accès à l'application

    Args:
        subject (Union[str, Any]): identifiant de l'utilisateur (généralement son ID ou son email)

    Returns:
        str: jeton d'accès encodé
    """
    expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "jti": str(uuid.uuid4())}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def _prepare_password(password: str) -> bytes:
    """Prépare le mot de passe en le hachant en SHA-256 pour contourner la limite des 72 octets de bcrypt.

    Args:
        password (str): mot de passe en clair à préparer pour le hachage

    Returns:
        bytes: mot de passe préparé (haché en SHA-256) prêt à être utilisé avec bcrypt
    """
    return hashlib.sha256(password.encode("utf-8")).digest()

def get_password_hash(password: str) -> str:
    """Retourne le hash d'un mot de passe

    Args:
        password (str): mot de passe en clair à hasher

    Returns:
        str: hash du mot de passe
    """
    prepared = _prepare_password(password)
    
    # Génération du sel et hachage
    # bcrypt.hashpw attend des bytes et retourne des bytes
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared, salt)

    # On décode en latin-1 pour le stocker proprement en String dans SQLite
    return hashed.decode('ascii')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérification d'un mot de passe par rapport à son hash

    Args:
        plain_password (str): mot de passe en clair à vérifier
        hashed_password (str): hash du mot de passe à comparer

    Returns:
        bool: True si le mot de passe correspond au hash, False sinon
    """
    try:
        prepared = _prepare_password(plain_password)
        # On encode le hash de la base en ascii pour bcrypt
        return bcrypt.checkpw(prepared, hashed_password.encode('ascii'))
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


async def validate_file_type(file: UploadFile):
    """Validation stricte du fichier uploadé pour éviter les risques de sécurité liés 
    à des fichiers malveillants.

    Args:
        file (UploadFile): Le fichier uploadé à valider.

    Raises:
        HTTPException: Aucun fichier sélectionné.
        HTTPException: Seuls les fichiers PDF et DOCX sont acceptés.
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
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les fichiers PDF et DOCX sont acceptés."
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
    
    if kind.mime not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fichier invalide, seuls les formats PDF et DOCX sont acceptés. Type détecté : {kind.mime}"
        )

    # 4. Vérification du Mot de Passe (Chiffrement)
    # On lit le fichier en mémoire pour pypdf (seulement les métadonnées)
    if kind.mime == "application/pdf":
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