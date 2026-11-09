from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import CATALOG, settings
from .router import available, choose, route

app = FastAPI(title="Multi-Model Router", version="0.1.0")


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    strategy: str | None = Field(None, description="rules | cheapest | quality | explicit")
    model: str | None = Field(None, description="required when strategy=explicit")
    max_tokens: int = Field(512, ge=1, le=8192)


@app.get("/health")      # Kubernetes liveness probe + Lambda smoke test
def health():
    return {"status": "ok"}


@app.get("/ready")       # Kubernetes readiness probe
def ready():
    return {"ready": bool(available()), "models": [m.name for m in available()]}


@app.get("/models")
def models():
    return [{**m.__dict__, "available": settings.has_key(m.provider)} for m in CATALOG]


@app.post("/route/preview")   # see the decision without spending tokens
def preview(req: ChatRequest):
    try:
        m, reason = choose(req.prompt, req.strategy or settings.default_strategy, req.model)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"model": m.name, "provider": m.provider, "reason": reason}


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        return await route(req.prompt, req.strategy, req.model, req.max_tokens)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(502, str(e))
