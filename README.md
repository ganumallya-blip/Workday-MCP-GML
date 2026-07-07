# Workday MCP Server - Phase 1

Production-oriented foundation for a reusable Workday-backed enterprise integration platform for employee digital assistants. Future clients may include Microsoft Copilot Studio, Microsoft 365 Copilot, ChatGPT, Claude, custom web/mobile assistants, and other MCP-compatible hosts.

Phase 1 intentionally implements only architecture foundation: configuration, Layer 1 identity abstraction, request context resolution, OAuth2 Authorization Code with PKCE, token/session abstraction, FastAPI callback handling, one MCP authentication tool, a Workday client scaffold, audit logging, and an admin operations console scaffold.

No PTO, leave, approval, worker profile, manager profile, events, or worker-search tools are implemented in Phase 1.

## Two Authentication Layers

This server separates authentication into two independent layers:

1. **Client / Copilot / MCP Host → MCP Server**: resolves the current assistant user through an `IdentityProvider` and produces a trusted `RequestContext`.
2. **MCP Server → Workday OAuth**: checks whether that resolved user has a valid Workday token session before calling Workday.

Being authenticated to the MCP server never means the user is already authenticated to Workday.

## Critical Identity Rule

The MCP server must never trust `user_id` values supplied by an LLM, assistant, or client tool argument. Identity comes only from authenticated request context.

The Phase 1 MCP tool is therefore:

```python
authenticate_workday()
```

It does **not** accept `user_id`. Future tools must follow the same pattern:

```python
context = await context_resolver.resolve(request)
await some_service.do_work(context, request_payload)
```

## Identity Providers

`src/identity/provider.py` defines the `IdentityProvider` interface and implementations:

- `DevIdentityProvider`: local development only.
- `FutureIdentityProvider`: placeholder for production authentication.

When `APP_ENV=local`, development identity resolves from:

1. `X-Dev-User` header when available.
2. `DEV_USER_ID` otherwise.

Development identity also supports `DEV_USER_EMAIL` and `DEV_USER_DISPLAY_NAME`. If `APP_ENV` is not `local`, `X-Dev-User` is rejected. Production TODOs include Entra ID JWT validation, Copilot Studio authentication, and generic OAuth/JWT validation.

In stdio/local MCP mode, the MCP SDK may not expose an HTTP request object. In that case, Phase 1 uses `DEV_USER_ID` through `DevIdentityProvider` for local development only.

## Request Context

`RequestContext` contains:

- `request_id`
- `user: UserIdentity`
- optional `client_type`
- optional `correlation_id`

All tool and service flows should receive `RequestContext` rather than raw user IDs.

## OAuth Flow

1. The assistant calls `authenticate_workday()`.
2. The server resolves the current user from request context or local development identity.
3. If no valid Workday token session exists, the MCP tool generates an authorization URL with state and PKCE S256 challenge.
4. OAuth state is stored in an expiring `OAuthStateStore` and bound to the resolved `user_id`.
5. The employee signs in to Workday using their own account.
6. Workday redirects to `GET /oauth/callback?code=...&state=...`.
7. The callback validates state, exchanges the authorization code with the PKCE verifier, and stores the token session for the user bound to state.
8. Future Workday calls use `OAuthManager.get_valid_access_token(context.user)`, refreshing when possible.

The implementation never logs access tokens, refresh tokens, authorization codes, client secrets, PKCE verifiers, or admin passwords.

## MCP Auth Tool

Phase 1 registers only:

```python
authenticate_workday()
```

Authenticated response:

```json
{"status": "authenticated", "message": "Already authenticated."}
```

Authentication-required response:

```json
{"status": "authentication_required", "authorization_url": "...", "message": "Please sign in to Workday."}
```

## Admin Console Boundaries

The admin API is mounted under `/admin` and is intended only for operations, security, and monitoring.

Available endpoints:

- `POST /admin/login`
- `GET /admin/health`
- `GET /admin/tools`
- `GET /admin/config/status`
- `GET /admin/sessions`
- `POST /admin/sessions/{user_id}/revoke`
- `GET /admin/audit/events`

Admins can view health, registered MCP tools, safe config status, safe token metadata, revoke sessions by safe session metadata key, and view audit events.

Admins cannot impersonate users, execute employee tools, run Workday APIs as employees, bypass Workday authorization, or see raw access tokens, refresh tokens, authorization codes, PKCE verifiers, client secrets, or passwords. There is intentionally no "run as user" feature.

Phase 1 uses local session-token admin auth. Set `ADMIN_PASSWORD_HASH` for non-local use. Supplying only `ADMIN_PASSWORD` is accepted only when `APP_ENV=local`. Replace this with Entra ID or enterprise SSO in a future phase.

## Environment Setup

Copy `.env.example` to `.env` and populate values from your Workday OAuth application and deployment environment.

```bash
cp .env.example .env
```

Key development identity values:

```bash
DEV_AUTH_ENABLED=true
DEV_USER_ID=local-dev-user
DEV_USER_EMAIL=local-dev-user@example.com
DEV_USER_DISPLAY_NAME="Local Dev User"
```

Required Workday values include authorize/token URLs, client ID, client secret, redirect URI, and scopes. Do not hardcode tenant names, URLs, client identifiers, secrets, scopes, or passwords in code.

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

- Accept business payloads only, not user identity arguments.
- Resolve `RequestContext` through `ContextResolver`.
- Use `OAuthManager.get_valid_access_token(context.user)`.
- Use `WorkdayClient` rather than duplicating HTTP logic.
- Preserve per-employee authorization and never use an integration-user token.
- Add audit events for security-relevant actions.
- Avoid exposing raw Workday tokens in logs, admin APIs, or tool responses.
