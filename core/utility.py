import asyncio
from pathlib import Path


from core.logging import logger
from dependencies.sqlite_session import SessionLocalSync
from repositories.job_repository import cleanup_old_jobs
from repositories.user_repository import cleanup_blacklisted_tokens


def delete_file(file_path: Path) -> bool:
    """Suppression d'un fichier

    Args:
        file_path (Path): chemin du fichier à supprimer

    Raises:
        ValueError: Erreur lors de la suppression du fichier

    Returns:
        bool: True si le fichier a été supprimé
    """
    try:
        # Suppression du fichier temporaire
        file_path.unlink()
        return True
    except Exception as e:
        raise ValueError(e)
    
async def schedule_periodic_cleanup(interval_seconds: int, days_to_keep: int):
    """Nettoyage périodique des jobs

    Args:
        interval_seconds (int): interval entre les nettoyages en seconde
        days_to_keep (int): nombre de jours à garder
    """
    while True:
        try:
            # On attend l'intervalle (ex: 24h)
            await asyncio.sleep(interval_seconds)
            
            with SessionLocalSync() as session:
                count = cleanup_old_jobs(session, days=days_to_keep)
                logger.info(f"Nettoyage automatique : {count} jobs supprimés.")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage automatique : {e}")
            # En cas d'erreur, on attend un peu avant de réessayer pour éviter de boucler sur un crash
            await asyncio.sleep(60)

async def blacklisted_token_cleanup(interval_seconds: int):
    """Nettoyage périodique des tokens blacklistés

    Args:
        interval_seconds (int): interval entre les nettoyages en seconde
    """
    while True:
        try:
            # On attend l'intervalle (ex: 24h)
            await asyncio.sleep(interval_seconds)
            
            with SessionLocalSync() as session:
                count = cleanup_blacklisted_tokens(session)
                logger.info(f"Nettoyage automatique : {count} tokens blacklistés supprimés.")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage automatique des tokens blacklistés : {e}")
            # En cas d'erreur, on attend un peu avant de réessayer pour éviter de boucler sur un crash
            await asyncio.sleep(60)