import asyncio
from contextlib import asynccontextmanager
from app.delivery import deliver_paid_orders
import logging
from fastapi import FastAPI
from app.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(deliver_paid_orders())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="Payment Service", lifespan=lifespan)
app.include_router(router)


@app.get("/api/payment/health")
@app.get("/health")
async def health():
    return {"service": "payment", "status": "ok"}
