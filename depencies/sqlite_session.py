from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.database import engine

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Dépendance pour obtenir une session de base de données asynchrone"""
    async with AsyncSessionLocal() as session:
        yield session
