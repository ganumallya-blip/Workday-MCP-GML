"""Admin operations API. This API never exposes secrets or employee tokens."""
from fastapi import APIRouter, Depends, HTTPException
from src.admin.auth import admin_auth_service, require_admin
from src.admin.schemas import AdminAuthenticationFailed, AdminHealthResponse, AdminLoginRequest, AdminLoginResponse
from src.audit.models import AuditEvent
from src.services import audit_logger, oauth_manager, settings, token_store

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/login", response_model=AdminLoginResponse)
async def login(request: AdminLoginRequest) -> AdminLoginResponse:
    try:
        token, ttl = await admin_auth_service.login(request.username, request.password)
        return AdminLoginResponse(access_token=token, expires_in_seconds=ttl)
    except AdminAuthenticationFailed as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

@router.get("/health", response_model=AdminHealthResponse)
async def health(_: str = Depends(require_admin)) -> AdminHealthResponse:
    return AdminHealthResponse(status="ok", admin_auth_enabled=settings.admin_auth_enabled)

@router.get("/tools")
async def tools(_: str = Depends(require_admin)) -> dict[str, list[str]]:
    return {"tools": ["authenticate_workday"]}

@router.get("/config/status")
async def config_status(_: str = Depends(require_admin)) -> dict[str, bool]:
    return settings.config_status()

@router.get("/sessions")
async def sessions(admin_user: str = Depends(require_admin)):
    await audit_logger.log(AuditEvent(event_type="admin", actor_type="admin", actor_id=admin_user, action="admin_viewed_sessions", status="success"))
    return await token_store.list_metadata()

@router.post("/sessions/{user_id}/revoke")
async def revoke_session(user_id: str, admin_user: str = Depends(require_admin)) -> dict[str, str]:
    await oauth_manager.revoke_token(user_id)
    await audit_logger.log(AuditEvent(event_type="admin", actor_type="admin", actor_id=admin_user, action="admin_revoked_session", target_user_id=user_id, status="success"))
    return {"status": "revoked", "user_id": user_id}

@router.get("/audit/events")
async def audit_events(_: str = Depends(require_admin), limit: int = 100):
    return await audit_logger.list_events(limit=limit)
