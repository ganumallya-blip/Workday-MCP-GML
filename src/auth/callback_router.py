"""FastAPI router for OAuth callbacks."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from src.auth.exceptions import AuthenticationRequired, InvalidOAuthState
from src.services import oauth_manager

router = APIRouter(prefix="/oauth", tags=["oauth"])

@router.get("/callback", response_class=PlainTextResponse)
async def oauth_callback(code: str = Query(...), state: str = Query(...)) -> str:
    try:
        await oauth_manager.exchange_authorization_code(code=code, state=state)
        return "Workday connected successfully. You may return to your assistant."
    except InvalidOAuthState as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AuthenticationRequired as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
