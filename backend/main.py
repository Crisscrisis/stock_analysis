import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from crawler.scheduler import shutdown_scheduler, start_scheduler
from database import AsyncSessionLocal, init_db
from routers import capital_flow, fundamentals, indicators, indices, stocks, watchlist, ws

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler = await start_scheduler(AsyncSessionLocal)
    yield
    await shutdown_scheduler(scheduler)


app = FastAPI(title="Stock Analysis API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(indicators.router, prefix="/api/indicators", tags=["indicators"])
app.include_router(fundamentals.router, prefix="/api/fundamentals", tags=["fundamentals"])
app.include_router(capital_flow.router, prefix="/api/capital-flow", tags=["capital-flow"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(indices.router, prefix="/api/indices", tags=["indices"])
app.include_router(ws.router, tags=["websocket"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
