import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL", "").strip()
publishable_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()

def make_client(key: str):
    if not url or not key:
        return None
    return create_client(url, key)

supabase_auth = make_client(publishable_key)
supabase_admin = make_client(service_role_key)

print("SUPABASE_URL loaded:", bool(url))
print("PUBLISHABLE loaded:", bool(publishable_key), publishable_key[:20] if publishable_key else None)
print("SERVICE_ROLE loaded:", bool(service_role_key), service_role_key[:20] if service_role_key else None)