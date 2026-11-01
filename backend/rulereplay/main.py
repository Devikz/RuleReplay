from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from rulereplay.api import router
from rulereplay.config import ConfigurationError, Settings, get_settings
from rulereplay.generation import GenerationError
from rulereplay.lifecycle import configure_logging
from rulereplay.operations import OperationError, Operations
from rulereplay.security import LocalBoundary
from rulereplay.storage import RecordError


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings if settings is not None else get_settings()
    configure_logging()
    app = FastAPI(title="RuleReplay", version="0.1.0", debug=False)
    app.state.settings = config
    app.state.operations = Operations(config)
    app.add_middleware(LocalBoundary, max_bytes=config.max_request_bytes)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"]
    )
    app.include_router(router)

    @app.exception_handler(OperationError)
    async def operation_error(_request, exc):
        return JSONResponse(
            status_code=exc.status, content={"detail": str(exc), "code": "operation_rejected"}
        )

    @app.exception_handler(OSError)
    async def storage_error(_request, _exc):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Local storage is unavailable. Review operation state before retrying.",
                "code": "storage_unavailable",
                "correlation_id": getattr(_request.state, "correlation_id", None),
            },
        )

    @app.exception_handler(Exception)
    async def unexpected_error(_request, _exc):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Analysis failed unexpectedly; no verification approval was issued.",
                "code": "internal_error",
                "correlation_id": getattr(_request.state, "correlation_id", None),
            },
        )

    @app.exception_handler(ConfigurationError)
    async def configuration_error(_request, exc):
        return JSONResponse(
            status_code=409, content={"detail": str(exc), "code": "configuration_error"}
        )

    @app.exception_handler(GenerationError)
    async def generation_error(_request, exc):
        return JSONResponse(
            status_code=502, content={"detail": str(exc), "code": "generation_failed"}
        )

    @app.exception_handler(RecordError)
    async def record_error(_request, exc):
        return JSONResponse(
            status_code=409, content={"detail": str(exc), "code": "invalid_evidence"}
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request, exc):
        # FastAPI's default response echoes invalid input, which could include pasted secrets.
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Invalid request. Check fields, dates, source mode and size limits.",
                "code": "invalid_request",
                "fields": [".".join(str(part) for part in e["loc"]) for e in exc.errors()],
            },
        )

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "service": "RuleReplay",
            "version": "0.1.0",
            "integrations": config.public_status(),
        }

    return app
