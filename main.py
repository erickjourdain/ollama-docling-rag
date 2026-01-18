import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from core.init import init_app
from routers import router_collection, router_insert, router_query, router_system
from core.config import settings

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Paramètres de l'application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
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

# Bootstrap de l'application
init_app()

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