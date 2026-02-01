import os
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from core.init import init_app
from routers import router_collection, router_insert, router_query, router_system
from core.config import settings
from services.db_vectorielle_service import DbVectorielleService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_app()
    app.state.vector_db_service = DbVectorielleService(
        chroma_db_dir=settings.chroma_db_dir,
        embedding_model=settings.llm_embedding_model,
        ollama_url=os.environ.get("OLLAMA_API_URL", "http://localhost:11434") 
    )
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
print("Allowed CORS origins:", origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files configuration
app.mount(settings.static_url, StaticFiles(directory=settings.static_dir), name="data")


# Insertion des routes
app.include_router(router_query)
app.include_router(router_collection)
app.include_router(router_insert)
app.include_router(router_system)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)