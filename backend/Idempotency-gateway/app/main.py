from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router

app = FastAPI(
    title="Idempotency Gateway",
    description="A payment API that processes each transaction exactly once, even if the client retries.",
    version="1.0.0",
    docs_url="/docs",    # interactive API docs available at /docs
    redoc_url="/redoc",
)

# Allow requests from any domain (fine for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Cache-Hit", "X-Idempotency-Key"],
)

app.include_router(router)
