# Workday MCP Server - Phase 1

Production-oriented foundation for a Workday MCP server that powers an enterprise employee digital assistant.

Phase 1 intentionally implements only the platform foundation: configuration, OAuth2 Authorization Code with PKCE, token/session abstraction, FastAPI callback handling, one MCP authentication tool, a Workday client scaffold, audit logging, and an admin operations console scaffold.

## Architecture

Employees authenticate with their own Workday accounts. Every future Workday request must execute with the requesting employee's access token. This is not an integration-user architecture, and admins cannot impersonate employees.

Core layers:

- `src/config.py` loads settings from environment variables only.
- `src/auth/` owns OAuth2, PKCE, token models, token store abstractions, and callback routing.
- `src/server.py` exposes the FastMCP server.
- `src/tools/auth_tools.py` contains the single Phase 1 MCP tool: `authenticate_workday`.
- `src/workday/client.py` provides authenticated `_get` and `_post` scaffolding for Phase 2 business tools.
- `src/admin/` exposes operations, security, and monitoring APIs.
- `src/audit/` records safe audit events without secrets or tokens.

## Project Structure

```text
src/
  main.py
  server.py
  config.py
  auth/
  admin/
  audit/
  workday/
  services/
  tools/
  utils/
tests/
  test_pkce.py
  test_token_store.py
```

## OAuth Flow

1. The assistant calls `authenticate_workday(user_id)`.
2. If no valid session exists, the MCP tool generates an authorization URL with state and PKCE S256 challenge.
3. The employee signs in to Workday using their own account.
4. Workday redirects to `GET /oauth/callback?code=...&state=...`.
5. The callback validates state, exchanges the authorization code with the PKCE verifier, and stores the token session.
6. Future requests use `OAuthManager.get_valid_access_token(user_id)`, which returns a valid token or refreshes when possible.

The implementation never logs access tokens, refresh tokens, authorization codes, client secrets, PKCE verifiers, or admin passwords.

## MCP Auth Tool

Phase 1 registers only:

```python
authenticate_workday(user_id: str)
```

Authenticated response:

```json
{"status": "authenticated", "message": "Already authenticated."}
```

Authentication-required response:

```json
{"status": "authentication_required", "authorization_url": "...", "message": "Please sign in to Workday."}
```

No PTO, leave, approval, worker, manager, event, or worker-search tools are implemented in Phase 1.

## Admin Console

The admin API is mounted under `/admin` and is intended only for operations, security, and monitoring.

Available endpoints:

- `POST /admin/login`
- `GET /admin/health`
- `GET /admin/tools`
- `GET /admin/config/status`
- `GET /admin/sessions`
- `POST /admin/sessions/{user_id}/revoke`
- `GET /admin/audit/events`

Admins can view health, registered MCP tools, safe config status, safe token metadata, revoke sessions, and view audit events. Admin APIs never return raw access tokens, refresh tokens, authorization codes, client secrets, or passwords. Admins cannot run tools as employees or impersonate users.

Phase 1 uses local session-token admin auth. Set `ADMIN_PASSWORD_HASH` for non-local use. Supplying only `ADMIN_PASSWORD` is accepted only when `APP_ENV=local`. Replace this with Entra ID or enterprise SSO in a future phase.

## Environment Setup

Copy `.env.example` to `.env` and populate values from your Workday OAuth application and deployment environment.

```bash
cp .env.example .env
```

Required variables include Workday authorize/token URLs, client ID, client secret, redirect URI, scopes, token encryption key, and admin session secret. Do not hardcode tenant names, URLs, client identifiers, secrets, scopes, or passwords in code.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run FastAPI App

```bash
uvicorn src.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

## Run MCP Server

```bash
python -m src.server
```

## Run Tests

```bash
pytest
```

## Extending in Phase 2

Add Workday business tools only after this foundation is validated. Future tools should:

- Require a `user_id` and call `OAuthManager.get_valid_access_token(user_id)`.
- Use `WorkdayClient` rather than duplicating HTTP logic.
- Preserve per-employee authorization and never use an integration-user token.
- Add audit events for security-relevant actions.
- Avoid exposing raw Workday tokens in logs, admin APIs, or tool responses.

Potential Phase 2 features may include PTO balance, leave requests, approvals, worker profile, manager profile, events, and worker search, but they are intentionally excluded from Phase 1.
