from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routes import router as api_v1_router
from app.core.config import settings

app = FastAPI(title="Knowledge Assistant API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def reject_cross_origin_cookie_writes(request: Request, call_next):  # noqa: ANN001, ANN201
    if request.method not in {"GET", "HEAD", "OPTIONS"} and request.cookies.get(settings.session_cookie_name):
        origin = request.headers.get("origin")
        if origin is not None and origin not in settings.cors_origin_list:
            return JSONResponse(status_code=403, content={"detail": "Cross-origin request rejected."})
    return await call_next(request)


app.include_router(api_v1_router)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model,
        "gemini_api_key_configured": bool(settings.gemini_api_key),
    }
