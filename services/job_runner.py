import asyncio
from typing import Callable, Any

from core.logging import logger
from core.config import settings

class JobRunner:

    def __init__(self):
        self.queue = asyncio.Queue()
        self.running = False
        self.semaphore = asyncio.Semaphore(settings.MAX_WORKER)

    async def start(self):
        if self.running:
            return
        
        self.running = True

        while True:
            job_func, kwargs = await self.queue.get()

            try:
                await job_func(**kwargs)
            except Exception as e:
                print(f"Job error: {e}")
                logger.error(f"Erreur lors de l'exécution du Job: {e}")

            self.queue.task_done()

    async def submit(self, job_func: Callable, **kwargs: Any):
        await self.queue.put((job_func, kwargs))