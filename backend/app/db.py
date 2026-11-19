import httpx
from .config import settings

BASE = f"{settings.SUPABASE_URL}/rest/v1"
HEADERS = {
    "apikey": settings.SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
}

# One shared client: reuses the SSL connection (fewer handshakes)
# and retries failed connects automatically.
client = httpx.Client(
    transport=httpx.HTTPTransport(retries=3),
    timeout=httpx.Timeout(30.0, connect=30.0),
)

def sb(method: str, table: str, params=None, json=None, prefer=None):
    h = dict(HEADERS)
    if prefer:
        h["Prefer"] = prefer
    r = client.request(method, f"{BASE}/{table}", headers=h,
                       params=params, json=json)
    if r.status_code >= 400:
        raise RuntimeError(f"DB error {r.status_code}: {r.text}")
    return r.json() if r.content else []

def select(table, **filters):
    params = {"select": "*"}
    params.update(filters)
    return sb("GET", table, params=params)

def insert(table, row):
    out = sb("POST", table, json=row, prefer="return=representation")
    return out[0] if out else None

def update(table, row_id, patch):
    out = sb("PATCH", table, params={"id": f"eq.{row_id}"},
             json=patch, prefer="return=representation")
    return out[0] if out else None