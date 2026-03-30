from sqlalchemy import select, func
from sqlalchemy.orm import Session

from db.models import Job, Query, User, CollectionMetadata
from schemas import QueryModel, QueryListResponse


def get_user_collection(
    session: Session,
    collection_id: str,
    user_id: str
) ->  QueryListResponse:
    """liste paginée des requêtes

    Args:
        session_session (Session): session sqlite
        collection_id: identifiant de la collection
        user_id: identfiant de l'utilisateur
    Returns:
        QueryListResponse: liste de requêtes et leur nombre total
    """
    stmt = select(Query).where(Query.user == user_id and Query.collection == collection_id)
    stmt_count = select(func.count(Query.id)).where(Query.user == user_id and Query.collection == collection_id)
    result = session.execute(stmt)
    result_count = session.execute(stmt_count).scalar_one()
    return QueryListResponse(
        data=[QueryModel.model_validate(c) for c in result.scalars().all()],
        count=result_count
    )

def get_by_job(
    session: Session,
    job_id: str
) -> Query | None:
    """Obtenir une requête via son job d'éxecution

    Args:
        session (Session): session de connexion à la base de données sqlite
        job_id (str): identifiant du job

    Returns:
        QueryModel | None : requête recherchée ou None
    """
    stmt = select(Query).where(Query.job == job_id)
    result = session.execute(stmt)
    return result.scalar_one_or_none()

def create_query(
    session: Session,
    user_id: str,
    collection_name: str,
    job_id: str,
    question: str,
    answer: str,
    model: str
) -> None:
    """Créer une nouvelle entrée dans la table des requêtes

    Args:
        session (Session): session de connexion à la base de données sqlite
        user (str): identfiant de l'utilisateur connecté
        collection_name (str): nom de la collection interogée
        job (str): identifiant du job de création
        question (str): question posée
        answer (str): réponse
        model (str): modèle utilisée

    Returns:
        Query: Nouvel enregistrement
    """
    stmt = select(User).where(User.id == user_id)
    user = session.execute(stmt).scalar_one_or_none()
    stmt = select(CollectionMetadata).where(CollectionMetadata.name == collection_name)
    collection = session.execute(stmt).scalar_one_or_none()
    stmt = select(Job).where(Job.id == job_id)
    job = session.execute(stmt).scalar_one_or_none()
    if user is None or collection is None or job is None:
        return
    new_query = Query(
        user = user,
        collection = collection,
        job = job,
        question = question,
        answer = answer,
        model = model
    )
    session.add(new_query)