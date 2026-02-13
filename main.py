from concurrent.futures import ThreadPoolExecutor
import os

from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.exceptions import RAGException
from core.init import init_app
from core.logging import logger
from depencies.sqlite_session import SessionLocalSync
from routers import router_collection, router_insert, router_query, router_system, router_job
from core.config import settings
from services import UserService, DbVectorielleService

load_dotenv()

# Lifespan de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_app()
    app.state.vector_db_service = DbVectorielleService(
        chroma_db=settings.CHROMA_DB,
        embedding_model=settings.LLM_EMBEDDINGS_MODEL,
        ollama_url=settings.OLLAMA_URL
    )
    # Définition du nombre de workers disponibles pour l'application
    app.state.executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKER)
    # Création de l'administrateur au premier démarrage de l'application
    with SessionLocalSync() as session:
        UserService().create_first_admin(session=session)
    yield
    # Code de nettoyage si nécessaire

# Paramètres de l'application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan
)

# Configuration CORS
origins= [os.environ.get("FRONTEND_URL", "")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files configuration
app.mount(settings.STATIC_URL, StaticFiles(directory=settings.STATIC_DIR), name="data")

# Insertion des routes
app.include_router(router_query)
app.include_router(router_collection)
app.include_router(router_insert)
app.include_router(router_job)
app.include_router(router_system)

@app.exception_handler(RAGException)
async def rag_exception_handler(request: Request, exc: RAGException):
    logger.error(f"Erreur applicative: {exc.message} | Détail: {exc.detail}")
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.message,
            "detail": exc.detail,
            "path": request.url.path
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)