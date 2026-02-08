from sqlalchemy import create_engine
from core.config import settings

SYNC_DATABASE_URL = f"sqlite:///./{settings.sqlite_db_dir}"

sync_engine = create_engine(
    url=SYNC_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
