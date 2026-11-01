"""Local-only application boundary: explicit hosts/origins and bounded request bodies."""

from uuid import uuid4

from starlette.responses import JSONResponse

from rulereplay.lifecycle import event

ALLOWED_ORIGINS = {
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",  # Disposable offline browser-test server.
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
}


class LocalBoundary:
    def __init__(self, app, max_bytes=256000):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        correlation_id = uuid4().hex
        scope.setdefault("state", {})["correlation_id"] = correlation_id
        headers = dict(scope["headers"])
        origin = headers.get(b"origin", b"").decode("latin1")
        if origin and origin not in ALLOWED_ORIGINS:
            return await JSONResponse({"detail": "Untrusted browser origin."}, 403)(
                scope, receive, send
            )
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > self.max_bytes:
                return await JSONResponse(
                    {"detail": "Request exceeds configured size limit."}, 413
                )(scope, receive, send)
            chunks.append(chunk)
            if not message.get("more_body"):
                break
        sent = False

        async def bounded_receive():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        response_started = False

        async def secure_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                message["headers"] += [
                    (b"x-content-type-options", b"nosniff"),
                    (b"cache-control", b"no-store"),
                    (b"x-correlation-id", correlation_id.encode()),
                ]
            await send(message)

        try:
            await self.app(scope, bounded_receive, secure_send)
        except Exception as exc:
            # Contain unexpected route errors before the ASGI server can log raw traceback
            # values. Provider exceptions are sanitized earlier at their own boundary.
            event("request_failure", correlation_id, category=type(exc).__name__)
            if response_started:
                raise RuntimeError("Response interrupted; details suppressed.") from None
            await JSONResponse(
                {
                    "detail": "Analysis failed unexpectedly; no verification approval was issued.",
                    "code": "internal_error",
                    "correlation_id": correlation_id,
                },
                500,
            )(scope, bounded_receive, secure_send)
