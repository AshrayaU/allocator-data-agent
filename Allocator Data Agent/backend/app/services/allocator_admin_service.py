from __future__ import annotations

import httpx

from config.settings import settings

# ---------------------------------------------------------------------------
# GET-only Allocator Admin API client.
#
# The Admin API exposes many write/import endpoints elsewhere in its spec
# (POST /cashflow_files/import, POST/PATCH/DELETE /security_master/*, etc. —
# see references/admin-api/admin-api-overview.md in the companion-app-guide
# skill for the full inventory). This app must NEVER call any of them. Every
# function below funnels through _AdminAPIClient, which:
#
#   1. Refuses any non-GET verb at the transport layer (`request()` below) —
#      even a future bug or a careless edit can't sneak a write through.
#   2. Exposes post/put/patch/delete methods that exist ONLY to raise a
#      clear, immediate error if anything ever calls them, rather than an
#      AttributeError or (worse) a silent no-op.
#
# Do not add a generic request(method, path) passthrough to this file. Add
# one explicit function per endpoint this app actually uses, and make sure
# each one calls a `_get`-only client.
# ---------------------------------------------------------------------------


class _AdminAPIClient(httpx.Client):
    """An httpx.Client that can only ever send GET requests."""

    def request(self, method: str, url, *args, **kwargs):  # type: ignore[override]
        if method.upper() != "GET":
            raise PermissionError(
                f"Blocked: attempted {method.upper()} request to {url}. "
                "This app's Allocator Admin API client is GET-only by design "
                "— POST/PUT/PATCH/DELETE requests to the Admin API are never "
                "permitted here."
            )
        return super().request(method, url, *args, **kwargs)

    def _blocked(self, *_args, **_kwargs):
        raise PermissionError(
            "Blocked: this Admin API client is GET-only by design. If a "
            "write operation is ever genuinely needed, it must be added "
            "deliberately with explicit review — never silently."
        )

    post = put = patch = delete = _blocked


def _auth() -> httpx.BasicAuth:
    """HTTP Basic auth for the Allocator Admin API.

    Verified empirically against GET /whoami (see docs/ADMIN_API_NOTES.md):
    username = SECRET_KEY, password = Admin AuthToken — matching the live
    Swagger docs, not the vendored template (which had it backwards).
    """
    return httpx.BasicAuth(settings.ALLOCATOR_ADMIN_SECRET_KEY, settings.ALLOCATOR_ADMIN_AUTH_TOKEN)


def _client() -> _AdminAPIClient:
    return _AdminAPIClient(base_url=settings.ALLOCATOR_API_BASE.rstrip("/"), auth=_auth(), timeout=15)


def get_investors(page: int = 1, per_page: int = 200) -> dict:
    """GET /investors — paginated list of investors."""
    with _client() as client:
        response = client.get("/investors", params={"page": page, "per_page": per_page})
        response.raise_for_status()
        return response.json()


def get_funds(page: int = 1, per_page: int = 200) -> dict:
    """GET /funds — paginated list of funds."""
    with _client() as client:
        response = client.get("/funds", params={"page": page, "per_page": per_page})
        response.raise_for_status()
        return response.json()


def whoami() -> dict:
    """GET /whoami — used only to sanity-check credentials, never by the login flow
    (login has its own direct call — see app/routes/auth.py)."""
    with _client() as client:
        response = client.get("/whoami")
        response.raise_for_status()
        return response.json()
