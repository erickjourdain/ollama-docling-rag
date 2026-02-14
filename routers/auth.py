from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.security import create_access_token, verify_password
from core.logging import logger
from db.models import User
from dependencies.sqlite_session import get_db
from dependencies.role_checker import allow_admin
from schemas.user import UserCreate, UserOut, UserToken
from services import UserService


router_auth = APIRouter(prefix="/auth", tags=["Authentication"])

@router_auth.post(
    "/login",
    response_model=UserToken,
    summary="Connexion à l'API",
    description="Connexion à l'API avec nom d'utilisateur et mot de passe."
)
async def login(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> UserToken:
    """Route de connexion à l'API

    Args:
        db (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).
        form_data (OAuth2PasswordRequestForm, optional): données de formulaire de connexion. Defaults to Depends().

    Raises:
        HTTPException: lève une exception HTTP 401 si les identifiants sont incorrects.

    Returns:
        _type_: un dictionnaire contenant le token d'accès et le type de token.
    """
    # 1. Chercher l'utilisateur
    user = UserService.get_user_by_name(session=db, username=form_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur inconnu"
        )
    
    # 2. Vérifier password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Générer le token
    access_token = create_access_token(subject=user.id)
    return UserToken(access_token=access_token, token_type="bearer")

@router_auth.post(
    "/logout",
    summary="Déconnexion de l'API",
    description="Déconnexion de l'API en invalidant le token d'accès."
)
async def logout(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="auth/login")), 
    session: Session = Depends(get_db)
) -> bool:
    """Route de déconnexion de l'API

    Args:
        token (str, optional): token d'accès à invalider. Defaults to Depends(OAuth2PasswordBearer).
        session (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).

    Raises:
        HTTPException: lève une exception HTTP 500 si une erreur survient lors de la déconnexion.

    Returns:
        _type_: un dictionnaire contenant le résultat de la déconnexion.
    """
    try:
        UserService.blacklist_token(session=session, token=token)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la déconnexion"
        )

@router_auth.post(
    "/create",
    response_model=UserOut,
    summary="Créer un nouvel utilisateur",
    description="Créer un nouvel utilisateur le mot de passe doit contenir au moins une majuscule, une minuscule, un chiffre et un caractère spécial."
)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
) -> UserOut:
    """Route de création d'un nouvel utilisateur

    Args:
        username (str): nom d'utilisateur du nouvel utilisateur.
        email (str): email du nouvel utilisateur.
        password (str): mot de passe du nouvel utilisateur.
        db (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).

    Raises:
        HTTPException: lève une exception HTTP 400 si le nom d'utilisateur existe déjà.
        HTTPException: lève une exception HTTP 500 si une erreur survient lors de la création de l'utilisateur.

    Returns:
        _type_: un dictionnaire contenant les informations de l'utilisateur créé.
    """
    # Vérifier si le nom d'utilisateur existe déjà
    existing_user = UserService.check_existing_user(
        session=db, 
        username=user.username,
        email=user.email
    )
    if existing_user:
        logger.warning(f"Tentative de création d'utilisateur avec un nom ou email existant: {user.username} / {user.email}")    
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nom d'utilisateur ou l'email existe déjà"
        )
    
    # Créer le nouvel utilisateur
    new_user = UserService.create_user(session=db, user=user, is_active=False)
    if new_user is None:
        logger.error(f"Erreur lors de la création de l'utilisateur: {user.username} / {user.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création de l'utilisateur"
        )    
    return UserOut.model_validate(new_user)

@router_auth.get("/activate/{user_id}")
async def activate_user(
    user_id: str,
    admin_user: User = Depends(allow_admin), 
    db: Session = Depends(get_db)
) -> bool:
    """Route d'activation d'un utilisateur

    Args:
        user_id (str): id de l'utilisateur à activer.
        db (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).

    Raises:
        HTTPException: lève une exception HTTP 404 si l'utilisateur n'est pas trouvé.
        HTTPException: lève une exception HTTP 500 si une erreur survient lors de l'activation de l'utilisateur.

    Returns:
        _type_: un dictionnaire contenant les informations de l'utilisateur activé.
    """
    user = UserService.activate_user(session=db, user_id=user_id)
    if user is None:
        logger.error(f"Tentative d'activation d'un utilisateur inconnu: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de l'activation de l'utilisateur"
        )    
    return True