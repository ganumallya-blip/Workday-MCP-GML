"""FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.admin.router import router as admin_router
from src.auth.callback_router import router as callback_router
from src.auth.exceptions import AuthenticationRequired, InvalidOAuthState
from src.config import get_settings
from src.utils.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title="Workday MCP Server", version="0.1.0")
app.include_router(callback_router)
app.include_router(admin_router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.exception_handler(AuthenticationRequired)
async def auth_required_handler(_: Request, exc: AuthenticationRequired) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})

@app.exception_handler(InvalidOAuthState)
async def invalid_state_handler(_: Request, exc: InvalidOAuthState) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})
