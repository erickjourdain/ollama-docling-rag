from sqlalchemy.orm import sessionmaker
#from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

#from db.database import engine, sync_engine
from db.database import sync_engine

#AsyncSessionLocal = async_sessionmaker(
#    bind=engine,
#    class_=AsyncSession,
#    expire_on_commit=False
#)

SessionLocalSync = sessionmaker(
    bind=sync_engine, 
    autocommit=False, 
    autoflush=False
)
 
#async def get_db_async():
#    """Dépendance pour obtenir une session de base de données asynchrone"""
#    async with AsyncSessionLocal() as session:
#        yield session

def get_db():
    with SessionLocalSync() as session:
        yield session