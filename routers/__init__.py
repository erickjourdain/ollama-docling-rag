from .query import router_query
from .system import router_system
from .insert import router_insert
from .collection import router_collection
from .job import router_job
from .auth import router_auth
from .user import router_user

__all__ = [
    "router_collection", 
    "router_insert", 
    "router_query", 
    "router_system",
    "router_job",
    "router_auth",
    "router_user"
]