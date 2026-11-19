import httpx
from app.config import settings

print("1) .env loaded OK")
print("   URL:", settings.SUPABASE_URL)
print("   Key starts with:", settings.SUPABASE_SERVICE_KEY[:12], "...")

r = httpx.get(
    f"{settings.SUPABASE_URL}/rest/v1/users",
    headers={
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
    },
    params={"select": "email,role", "limit": 10},
    timeout=20,
)
print("2) Supabase status:", r.status_code)
print("   Response:", r.text[:400])