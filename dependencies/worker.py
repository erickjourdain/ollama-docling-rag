from concurrent.futures import ThreadPoolExecutor
from fastapi import Request


def get_workers(request: Request) -> ThreadPoolExecutor:
    return request.app.state.executor