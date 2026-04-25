from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router

app = FastAPI(
    title="Pulse-Check API",
    description="A dead man's switch API that alerts you when a device stops sending heartbeats.",
    version="1.0.0",
    docs_url="/docs",    # interactive API docs at /docs
    redoc_url="/redoc",
)

# Allow requests from any domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
