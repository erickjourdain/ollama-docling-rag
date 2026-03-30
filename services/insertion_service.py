import asyncio
from pathlib import Path

from core.logging import logger
from dependencies.sqlite_session import SessionLocalSync
from schemas import CollectionModel, JobOut
from .user_websocket_manager import UserWebSocketManager
from worker.insert_doc import insert_doc
from repositories import job_repository

class InsertionService:

    @staticmethod
    async def run_insert_doc(
        job_id: str,
        user_id: str,
        file_path: Path,
        filename: str,
        doc_id: str,
        collection: CollectionModel,
        user_ws_manager: UserWebSocketManager
    ):
        """job d'insertion d'un document dans la base de données vectorielles

        Args:
            job_id (str): identifiant du job
            user_id (str): identifiant de l'utilisateur créateur du job
            file_path (str): chemin vers le fichier à insérer
            filename (str): nom du fichier à insérer
            doc_id (str): identifiant du document à insérer
            collection (CollectionModel): collection d'insertion
            ws_manager (UserWebSocketManager): manager des sockets utilisateurs
        """
        max_attempts = 3

        with SessionLocalSync() as session:
            job = job_repository.get_job(session=session, job_id=job_id)
            if job is None:
                logger.error(f"Job {job_id} inconnu")
                raise Exception("Aucun job avec cet identifiant dans la base")
            
            for attempt in range(1, max_attempts + 1):
                try:
                    job.attemps = attempt
                    session.commit()
                    await user_ws_manager.send_to_user(
                        user_id=user_id,
                        data=JobOut.model_validate(job)
                    )
                    await asyncio.wait_for(
                        insert_doc(
                            file_path=file_path,
                            filename=filename,
                            doc_id=doc_id,
                            collection=collection,
                            job_id=job_id,
                            user_id=user_id,
                            user_ws_manager=user_ws_manager
                        ),
                        timeout=300
                    )
                    job.status = "completed"
                    job.progress = "done"
                    session.commit()
                    await user_ws_manager.send_to_user(
                        user_id=user_id,
                        data=JobOut.model_validate(job)
                    )  
                    return

                except Exception as e:
                    if attempt >= max_attempts:
                        job.error_message = str(e)
                        session.commit()
                        await user_ws_manager.send_to_user(
                            user_id=user_id,
                            data=JobOut.model_validate(job)
                        )  
                        return
                    delay = 2 ** attempt
                    job.status = "retrying"
                    session.commit()
                    await user_ws_manager.send_to_user(
                        user_id=user_id,
                        data=JobOut.model_validate(job)
                    )
                    await asyncio.sleep(delay)