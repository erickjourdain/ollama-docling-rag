import logging
from fastapi import FastAPI
from core.init import init_app
from routers import router_collection, router_insert, router_query, router_system
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paramètres de l'application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
)

# Bootstrap de l'application
init_app()

# Insertion des routes
app.include_router(router_query)
app.include_router(router_collection)
app.include_router(router_insert)
app.include_router(router_system)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)