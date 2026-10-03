from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.db.session import engine
from app.db.base import Base
from app.db.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed if empty
    await seed_database()
    yield
    await engine.dispose()


app = FastAPI(
    title="Adaptive AI Tutor",
    description="Adaptive AI Tutor for Misinformation Literacy – Final Year Thesis Prototype",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "message": "Adaptive AI Tutor API is running",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}