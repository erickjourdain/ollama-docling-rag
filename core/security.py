import hashlib
from pathlib import Path
import bcrypt

def _prepare_password(password: str) -> bytes:
    """
    Prépare le mot de passe en le hachant en SHA-256 pour 
    contourner la limite des 72 octets de bcrypt.
    """
    return hashlib.sha256(password.encode("utf-8")).digest()

def hash_password(password: str) -> str:
    """Transformation du mot de passe en hash pour stockage"""
    prepared = _prepare_password(password)
    
    # Génération du sel et hachage
    # bcrypt.hashpw attend des bytes et retourne des bytes
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared, salt)

    # On décode en latin-1 pour le stocker proprement en String dans SQLite
    return hashed.decode('ascii')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe clair correspond au hash en base."""
    try:
        prepared = _prepare_password(plain_password)
        # On encode le hash de la base en ascii pour bcrypt
        return bcrypt.checkpw(prepared, hashed_password.encode('ascii'))
    except Exception:
        return False

def hash_file(file_path: Path, chunk_size: int=4096):
    """Hash d'un fichier"""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    return md5.hexdigest()

def verify_md5(file_path: Path, expected_hash: str, chunk_size: int=4096):
    """Vérifier le hash d'un fichier"""
    calculated_hash = hash_file(file_path, chunk_size)
    # Case-insensitive comparison is often needed
    return calculated_hash.lower() == expected_hash.lower()