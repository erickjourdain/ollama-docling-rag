import logging
from fastapi import FastAPI
from routers import router_collection, router_insert, router_query, router_system
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
)

app.include_router(router_query)
app.include_router(router_collection)
app.include_router(router_insert)
app.include_router(router_system)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)