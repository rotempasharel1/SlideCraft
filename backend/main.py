import os
from urllib.parse import quote

from google import genai
from google.genai import types
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse

from .database import supabase_auth, supabase_admin
from .models import ProjectCreate, EmailLoginRequest, ChatRequest, CourseGenerationResponse, DraftState

load_dotenv()

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "rotem.pasharel1@gmail.com").strip().lower()

app = FastAPI(title="Educational AI Platform API")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_AUTH_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8501")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in backend .env")

genai_client = genai.Client(api_key=GEMINI_API_KEY)

def require_supabase():
    if not SUPABASE_URL or not SUPABASE_AUTH_KEY or not SUPABASE_SERVICE_KEY:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    if not supabase_auth or not supabase_admin:
        raise HTTPException(status_code=500, detail="Supabase clients not configured")


def get_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    return authorization.split(" ", 1)[1].strip()


def get_auth_user(access_token: str) -> dict:
    require_supabase()

    try:
        res = requests.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "apikey": SUPABASE_AUTH_KEY,
            },
            timeout=20,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth request failed: {e}")

    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return res.json()


def sync_profile(auth_user: dict) -> dict:
    user_id = auth_user["id"]
    metadata = auth_user.get("user_metadata") or {}

    email = auth_user.get("email")
    email_normalized = (email or "").strip().lower()

    full_name = (
        metadata.get("full_name")
        or metadata.get("name")
        or metadata.get("user_name")
    )

    avatar_url = (
        metadata.get("avatar_url")
        or metadata.get("picture")
    )

    role = "admin" if email_normalized == ADMIN_EMAIL else "user"

    existing_res = supabase_admin.table("profiles").select("*").eq("id", user_id).execute()
    existing = existing_res.data[0] if existing_res.data else None

    if existing:
        update_data = {
            "email": email,
            "full_name": full_name,
            "avatar_url": avatar_url,
            "role": role,
        }
        supabase_admin.table("profiles").update(update_data).eq("id", user_id).execute()
        existing.update(update_data)
        return existing

    new_profile = {
        "id": user_id,
        "email": email,
        "full_name": full_name,
        "avatar_url": avatar_url,
        "role": role,
    }
    supabase_admin.table("profiles").insert(new_profile).execute()
    return new_profile


def get_current_profile(authorization: str | None) -> dict:
    access_token = get_bearer_token(authorization)
    auth_user = get_auth_user(access_token)
    return sync_profile(auth_user)


def require_admin(authorization: str | None) -> dict:
    profile = get_current_profile(authorization)
    if profile.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return profile


def enrich_projects_with_owner(projects: list[dict]) -> list[dict]:
    if not projects:
        return []

    owner_ids = list({p["owner_id"] for p in projects if p.get("owner_id")})
    if not owner_ids:
        return projects

    profiles_res = (
        supabase_admin.table("profiles")
        .select("id, email, full_name")
        .in_("id", owner_ids)
        .execute()
    )
    profiles_map = {p["id"]: p for p in (profiles_res.data or [])}

    enriched = []
    for project in projects:
        owner = profiles_map.get(project.get("owner_id"), {})
        item = dict(project)
        item["owner_name"] = owner.get("full_name")
        item["owner_email"] = owner.get("email")
        enriched.append(item)

    return enriched


@app.get("/auth/google/start")
def auth_google_start():
    require_supabase()

    redirect_to = f"{BACKEND_URL}/auth/google/callback"
    authorize_url = (
        f"{SUPABASE_URL}/auth/v1/authorize"
        f"?provider=google&redirect_to={quote(redirect_to, safe='')}"
    )
    return RedirectResponse(url=authorize_url, status_code=302)


@app.post("/auth/email/start")
def auth_email_start(payload: EmailLoginRequest):
    require_supabase()

    email = (payload.email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        supabase_auth.auth.sign_in_with_otp(
            {
                "email": email,
                "options": {
                    "should_create_user": True,
                    "email_redirect_to": f"{BACKEND_URL}/auth/google/callback",
                },
            }
        )
        return {"status": "ok", "message": "Magic link sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/google/callback", response_class=HTMLResponse)
def auth_google_callback():
    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>Signing you in...</title>
    </head>
    <body>
      <script>
        const hash = new URLSearchParams(window.location.hash.slice(1));
        const query = new URLSearchParams(window.location.search);

        const accessToken =
          hash.get("access_token") ||
          query.get("access_token");

        const errorDescription =
          hash.get("error_description") ||
          query.get("error_description") ||
          query.get("error") ||
          "Sign-in failed";

        const target = new URL("{FRONTEND_URL}");

        if (accessToken) {{
          target.searchParams.set("access_token", accessToken);
        }} else {{
          target.searchParams.set("auth_error", errorDescription);
        }}

        window.location.replace(target.toString());
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/me")
def me(authorization: str | None = Header(default=None)):
    try:
        profile = get_current_profile(authorization)
        return {
            "id": profile["id"],
            "email": profile.get("email"),
            "full_name": profile.get("full_name"),
            "avatar_url": profile.get("avatar_url"),
            "role": profile.get("role", "user"),
        }
    except Exception as e:
        print("PROFILE ERROR:", e)
        raise


@app.post("/chat/generate_course")
def generate_course(payload: ChatRequest):
    prompt = (payload.prompt or "").strip()
    context = (payload.context or "").strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    try:
        system_instructions = (
            "You are an expert AI teacher that builds educational courses chapter by chapter. "
            "STRICT OUTPUT RULES — you MUST follow these exactly:\n"
            "1. PAGES: Generate EXACTLY 5 detailed educational pages for this chapter. "
            "Each page must have a clear title and rich, thorough content in Markdown. "
            "Do NOT generate fewer than 5 pages under any circumstances.\n"
            "2. QUIZ: After the pages, create EXACTLY 5 multiple-choice questions that test "
            "understanding of the content just generated. Each question MUST have exactly 4 answer options. "
            "Do NOT skip the quiz.\n"
            "3. CHAT MESSAGE: Write a short message summarising this chapter, suggesting the next "
            "logical topic, and asking the user if they want to continue or finish and save.\n"
            "4. LANGUAGE: ALL output (titles, content, questions, options, explanations, chat message) "
            "MUST be in English only, regardless of the language the user writes in."
        )

        full_prompt = (
            f"Context/Previous Lesson context: {context}\n\n"
            f"User Prompt: {prompt}"
        )

        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instructions,
                temperature=0.7,
                top_p=0.95,
                max_output_tokens=16384,
                response_mime_type="application/json",
                response_schema=CourseGenerationResponse,
            ),
        )

        response_text = (response.text or "").strip()

        if not response_text:
            raise HTTPException(status_code=500, detail="Gemini returned an empty response.")

        import json
        structured_data = json.loads(response_text)

        return structured_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {e}")

@app.post("/chat/draft")
def save_chat_draft(
    draft: DraftState,
    authorization: str | None = Header(default=None)
):
    profile = get_current_profile(authorization)
    try:
        draft_content = draft.model_dump_json()
        
        # Check if draft already exists
        existing = supabase_admin.table("projects").select("id").eq("owner_id", profile["id"]).eq("title", "__DRAFT_STATE__").execute()
        
        if existing.data:
            response = supabase_admin.table("projects").update({"content": draft_content}).eq("id", existing.data[0]["id"]).execute()
        else:
            data = {
                "owner_id": profile["id"],
                "title": "__DRAFT_STATE__",
                "content": draft_content,
                "is_public": False,
            }
            response = supabase_admin.table("projects").insert(data).execute()
            
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/draft")
def load_chat_draft(authorization: str | None = Header(default=None)):
    profile = get_current_profile(authorization)
    try:
        response = supabase_admin.table("projects").select("content").eq("owner_id", profile["id"]).eq("title", "__DRAFT_STATE__").execute()
        if response.data:
            import json
            return json.loads(response.data[0]["content"])
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/chat/draft")
def delete_chat_draft(authorization: str | None = Header(default=None)):
    """Explicitly clear the draft — called when user starts a new course."""
    profile = get_current_profile(authorization)
    try:
        supabase_admin.table("projects").delete().eq("owner_id", profile["id"]).eq("title", "__DRAFT_STATE__").execute()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/shared")
def get_shared_projects():
    try:
        response = (
            supabase_admin.table("projects")
            .select("*")
            .eq("is_public", True)
            .order("created_at", desc=True)
            .execute()
        )
        return enrich_projects_with_owner(response.data or [])
    except Exception as e:
        print(f"DB Error: {e}")
        return []


@app.get("/projects/my")
def get_my_projects(authorization: str | None = Header(default=None)):
    profile = get_current_profile(authorization)

    try:
        response = (
            supabase_admin.table("projects")
            .select("*")
            .eq("owner_id", profile["id"])
            .neq("title", "__DRAFT_STATE__")
            .order("created_at", desc=True)
            .execute()
        )
        return enrich_projects_with_owner(response.data or [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/projects")
def save_project(
    project: ProjectCreate,
    authorization: str | None = Header(default=None),
):
    profile = get_current_profile(authorization)

    try:
        data = {
            "owner_id": profile["id"],
            "title": project.title,
            "content": project.content,
            "is_public": project.is_public,
        }
        response = supabase_admin.table("projects").insert(data).execute()
        return response.data[0] if response.data else {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/projects/{project_id}")
def update_project(
    project_id: str,
    project: ProjectCreate,
    authorization: str | None = Header(default=None),
):
    """Allow a user to update their own course content and title."""
    profile = get_current_profile(authorization)

    try:
        # Verify ownership
        check = (
            supabase_admin.table("projects")
            .select("id")
            .eq("id", project_id)
            .eq("owner_id", profile["id"])
            .execute()
        )
        if not check.data:
            raise HTTPException(status_code=404, detail="Course not found or no permission.")

        data = {
            "title": project.title,
            "content": project.content,
            "is_public": project.is_public,
        }
        response = supabase_admin.table("projects").update(data).eq("id", project_id).execute()
        return response.data[0] if response.data else {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/projects")
def get_all_projects(authorization: str | None = Header(default=None)):
    require_admin(authorization)

    try:
        response = (
            supabase_admin.table("projects")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return enrich_projects_with_owner(response.data or [])
    except Exception as e:
        print(f"DB Error: {e}")
        return []


@app.delete("/admin/projects/{project_id}")
def delete_project(
    project_id: str,
    authorization: str | None = Header(default=None),
):
    require_admin(authorization)

    try:
        response = supabase_admin.table("projects").delete().eq("id", project_id).execute()
        return {"status": "success", "deleted": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/projects/{project_id}")
def delete_my_project(
    project_id: str,
    authorization: str | None = Header(default=None),
):
    """Allow a user to delete their own course by ID."""
    profile = get_current_profile(authorization)

    try:
        # Make sure the project belongs to the current user
        check = (
            supabase_admin.table("projects")
            .select("id")
            .eq("id", project_id)
            .eq("owner_id", profile["id"])
            .execute()
        )
        if not check.data:
            raise HTTPException(status_code=404, detail="Course not found or you don't have permission to delete it.")

        response = supabase_admin.table("projects").delete().eq("id", project_id).execute()
        return {"status": "success", "deleted": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))