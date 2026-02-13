from sqlalchemy import create_engine, event
from core.config import settings

SYNC_DATABASE_URL = f"sqlite:///./{settings.SQLITE_DB}"

sync_engine = create_engine(
    url=SYNC_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

@event.listens_for(sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # Active le mode WAL
    cursor.execute("PRAGMA journal_mode=WAL")
    # Optimise la synchronisation (plus rapide)
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()
