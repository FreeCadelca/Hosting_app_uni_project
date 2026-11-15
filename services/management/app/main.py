import logging
from fastapi import FastAPI
from app.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Management Service")
app.include_router(router)


@app.get("/api/servers/health")
@app.get("/health")
async def health():
    return {"service": "management", "status": "ok"}
