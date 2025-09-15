from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .routers import auth, provisioning, stream

settings = get_settings()
app = FastAPI(title="Provisioning API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOW_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metrics_counter = {"requests": 0}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return metrics_counter


@app.middleware("http")
async def add_metrics(request, call_next):
    metrics_counter["requests"] += 1
    return await call_next(request)


app.include_router(auth.router)
app.include_router(provisioning.router)
app.include_router(stream.router)
