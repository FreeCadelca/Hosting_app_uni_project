import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.consumer import start_consumer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the RabbitMQ consumer as a background task
    task = asyncio.create_task(start_consumer())
    logger.info("Provisioning service started, consumer task launched")
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Provisioning Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"service": "provisioning", "status": "ok"}
