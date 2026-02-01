from sqlalchemy.ext.asyncio import create_async_engine
from core.config import settings

DATABASE_URL = f"sqlite+aiosqlite:///./{settings.sqlite_db_dir}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)