import html
import re
import json
import base64
import streamlit as st
import requests

# Backend API Base URL
API_URL = "http://127.0.0.1:8000"
GOOGLE_LOGIN_URL = f"{API_URL}/auth/google/start"

CARD_COLORS = [
    "linear-gradient(135deg, #1f78c1 0%, #3ca0f0 100%)",
    "linear-gradient(135deg, #f57c00 0%, #ff9f1c 100%)",
    "linear-gradient(135deg, #0b1f3a 0%, #174a82 100%)",
    "linear-gradient(135deg, #d47e13 0%, #f0a03c 100%)",
]

def simple_md_to_html(md_text: str) -> str:
    """Convert basic markdown to HTML for rendering inside HTML blocks."""
    # Strip any embedded JSON header before converting
    text = re.sub(r'^<!-- COURSE_PAGES_JSON\n.*?\n-->\n?', '', md_text, flags=re.DOTALL)
    text = html.escape(text)
    text = re.sub(r'^#{4} (.+)$', r'<h5 style="color:#1f2937;margin:0.5rem 0;">\1</h5>', text, flags=re.MULTILINE)
    text = re.sub(r'^#{3} (.+)$', r'<h4 style="color:#1f2937;margin:0.6rem 0;">\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^#{2} (.+)$', r'<h3 style="color:#1f2937;margin:0.7rem 0;">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$',    r'<h2 style="color:#1f2937;margin:0.8rem 0;">\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*',   r'<em>\1</em>', text)
    text = re.sub(r'^- (.+)$', r'<li style="color:#1f2937;margin:0.15rem 0;">\1</li>', text, flags=re.MULTILINE)
    text = text.replace('\n', '<br>')
    return text

st.set_page_config(
    page_title="EduBuilder AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

        * {
            font-family: 'Inter', sans-serif !important;
            direction: ltr !important;
        }

        html, body {
            direction: ltr !important;
        }

        @keyframes gradient_wave {
            0%   { background-position: 0% 50%; }
            25%  { background-position: 50% 100%; }
            50%  { background-position: 100% 50%; }
            75%  { background-position: 50% 0%; }
            100% { background-position: 0% 50%; }
        }

        .stApp {
            background: linear-gradient(
                -45deg,
                #0b1f3a,
                #123f6b,
                #1f78c1,
                #f57c00,
                #ff9f1c,
                #0b1f3a
            );
            background-size: 500% 500%;
            animation: gradient_wave 16s ease-in-out infinite;
            min-height: 100vh;
        }

        [data-testid="stHeader"] {
            background-color: transparent !important;
        }

        .main {
            background-color: transparent !important;
        }

        .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 2rem !important;
        }

        .stButton > button,
        .stFormSubmitButton > button {
            background: linear-gradient(135deg, #5b7cfa 0%, #8b5fbf 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.65rem 1rem !important;
            font-weight: 700 !important;
            transition: all 0.25s ease !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
            width: 100% !important;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 18px rgba(0,0,0,0.18) !important;
        }

        .stTextInput > div > div > input {
            border-radius: 10px !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            padding: 0.7rem 1rem !important;
            transition: all 0.2s ease !important;
            background-color: rgba(255,255,255,0.96) !important;
            color: #1f2937 !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: #8ab4ff !important;
            box-shadow: 0 0 0 3px rgba(138, 180, 255, 0.22) !important;
        }

        [data-testid="stWidgetLabel"] p {
            color: white !important;
            font-weight: 600 !important;
            margin-bottom: 0.25rem !important;
        }

        .stCheckbox label span {
            color: white !important;
        }

        .streamlit-expanderHeader {
            background-color: white !important;
            border-radius: 8px !important;
            border: 1px solid #e2e8f0 !important;
            font-weight: 600 !important;
            color: #2d3748 !important;
            transition: all 0.2s ease !important;
        }

        .streamlit-expanderHeader:hover {
            background-color: #f7fafc !important;
            border-color: #cbd5e0 !important;
        }

        div[data-testid="stExpanderDetails"] {
            background-color: rgba(255, 255, 255, 0.88) !important;
            border-radius: 0 0 8px 8px !important;
            padding: 1.5rem !important;
            border: 1px solid #e2e8f0 !important;
            border-top: none !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important;
        }

        [data-testid="stChatMessage"] {
            background-color: white !important;
            border-radius: 12px !important;
            padding: 1rem !important;
            margin-bottom: 1rem !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
            border: 1px solid #edf2f7 !important;
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background-color: #f0f4ff !important;
            border-color: #e2e8f0 !important;
        }

        h1, h2, h3 {
            color: white !important;
            font-weight: 700 !important;
            letter-spacing: -0.5px !important;
        }

        .auth-subtitle {
            text-align: center;
            color: rgba(255,255,255,0.9);
            font-size: 1.02rem;
            margin-top: -0.3rem;
            margin-bottom: 1.4rem;
        }

        .top-spacer {
            height: 2vh;
        }

        .google-login-link {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            padding: 0.85rem 1rem;
            border-radius: 12px;
            background: white;
            color: #1f2937 !important;
            text-decoration: none !important;
            font-weight: 700;
            font-size: 1rem;
            box-shadow: 0 6px 18px rgba(0,0,0,0.15);
            transition: all 0.25s ease;
            border: 1px solid rgba(255,255,255,0.35);
            box-sizing: border-box;
        }

        .google-login-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 22px rgba(0,0,0,0.18);
            color: #111827 !important;
        }

        .google-note {
            text-align: center;
            color: rgba(255,255,255,0.88);
            margin-top: 0.85rem;
            font-size: 0.95rem;
        }
         .user-card {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            background: transparent;
            border-radius: 0;
            padding: 0;
            margin-top: 0.4rem;
            margin-bottom: 0.8rem;
            box-shadow: none;
        }

        .user-initial {
            width: 48px;
            height: 48px;
            min-width: 48px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #1f78c1 0%, #3ca0f0 100%);
            color: white;
            font-weight: 800;
            font-size: 1.15rem;
        }

        .user-meta {
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .user-name {
            color: #111111;
            font-weight: 700;
            font-size: 0.98rem;
            line-height: 1.2;
        }

        .user-email {
            color: #333333;
            font-size: 0.85rem;
            line-height: 1.2;
            opacity: 0.9;
            word-break: break-word;
        }
        /* LTR Chat UI */
        [data-testid="stChatInput"] {
            direction: ltr;
        }

        /* ---------------- Course Viewer Styling ---------------- */
        
        .course-viewer-box {
            background: #ffffff !important;
            border-radius: 12px !important;
            border: 1px solid #ddd !important;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.12) !important;
            padding: 25px !important;
            margin-top: 15px !important;
            color: #111111 !important;
        }
        
        .course-viewer-box * {
            color: #111111 !important;
            background: transparent !important;
        }

        /* ---------------- Sidebar text colors ---------------- */
        
        .save-ready-note {
            text-align: center;
            color: white;
            font-weight: 600;
            margin-top: 1rem;
            margin-bottom: 0.25rem;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            color: #111111 !important;
        }

        /* ---------------- Custom Styled Sidebar Menu (Colored Boxes) ---------------- */
        
        [data-testid="stSidebar"] .stRadio > label {
            display: none !important; /* Hide the native label if it exists */
        }

        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
            gap: 0.8rem !important;
            padding-top: 0.5rem !important;
        }

        /* Base styles for the menu boxes */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
            padding: 0.85rem 1rem !important;
            border-radius: 12px !important;
            border: 2px solid transparent !important;
            cursor: pointer !important;
            transition: all 0.25s ease !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
        }

        /* Hide the radio circle (it is the first child div of the label) */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }
        
        /* Make text white and bold */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label p {
            font-weight: 700 !important;
            margin: 0 !important;
            color: white !important;
            font-size: 1.1rem !important;
            letter-spacing: 0.5px !important;
            text-align: center !important;
            width: 100% !important;
        }

        /* Item 1: Create Course (Blue) */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(1) {
            background: linear-gradient(135deg, #1f78c1 0%, #3ca0f0 100%) !important;
        }

        /* Item 2: My Courses (Orange) */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(2) {
            background: linear-gradient(135deg, #f57c00 0%, #ff9f1c 100%) !important;
        }

        /* Item 3: Shared Courses (Dark Blue) */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(3) {
            background: linear-gradient(135deg, #0b1f3a 0%, #174a82 100%) !important;
        }

        /* Item 4: Admin Panel (Light Amber) */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(4) {
            background: linear-gradient(135deg, #d47e13 0%, #f0a03c 100%) !important;
        }

        /* Hover effects */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 16px rgba(0,0,0,0.18) !important;
            filter: brightness(1.1) !important;
        }

        /* Active/Checked state */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input[type="radio"]:checked) {
            border: 2px solid #ffffff !important;
            box-shadow: 0 0 0 3px #111111, 0 8px 16px rgba(0,0,0,0.2) !important;
            transform: scale(1.03) !important;
            filter: brightness(1.15) !important;
        }
/* ---------------- Sidebar collapse/open arrow fix ---------------- */

/* Completely hide Streamlit native UI text, svgs, and spans inside the buttons */
[data-testid="collapsedControl"] > div,
[data-testid="collapsedControl"] > span,
[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] i,
[data-testid="stExpandSidebarButton"] > div,
[data-testid="stExpandSidebarButton"] > span,
[data-testid="stExpandSidebarButton"] svg,
[data-testid="stExpandSidebarButton"] i,
[data-testid="stSidebarCollapseButton"] > div,
[data-testid="stSidebarCollapseButton"] > span,
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapseButton"] i,
.st-emotion-cache-5r6ut5.exvv1vr0 {
    color: transparent !important;
    font-size: 0 !important;
    line-height: 0 !important;
}

/* Ensure the control container behaves as a button-like anchor */
[data-testid="collapsedControl"],
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"] {
    position: fixed !important; /* Force position fixed so it always floats! */
    top: 10px !important;       /* Space from top */
    left: 10px !important;      /* Space from left */
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 2.5rem !important;
    height: 2.5rem !important;
    background: transparent !important;
    border: none !important;
    z-index: 999999 !important; /* Force on top of everything! */
}

/* Force inject the right arrow on collapsed state */
[data-testid="collapsedControl"]::before,
[data-testid="stExpandSidebarButton"]::before {
    content: "▶" !important;
    position: absolute !important;
    left: 50% !important;
    top: 50% !important;
    transform: translate(-50%, -50%) !important;
    font-size: 26px !important;
    font-weight: 900 !important;
    color: #111111 !important;  /* Make the "open" arrow dark against the main background */
    text-shadow: 0 1px 2px rgba(255,255,255,0.8) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    pointer-events: none !important;
}

/* Force inject the left arrow correctly on expanded state */
[data-testid="stSidebarCollapseButton"]::before,
[data-testid="stSidebarCollapseButton"] button::before {
    content: "◀" !important;
    position: absolute !important;
    left: 50% !important;
    top: 50% !important;
    transform: translate(-50%, -50%) !important;
    font-size: 26px !important;
    font-weight: 900 !important;
    color: #111111 !important;
    text-shadow: 0 1px 2px rgba(255,255,255,0.5) !important;
    display: block !important;
    visibility: visible !important;
    pointer-events: none !important;
    z-index: 999999 !important;
}
        /* ---------------- White Course Viewer Area ---------------- */

        .course-viewer-anchor {
            display: none;
        }

        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) {
            background: #ffffff !important;
            border-radius: 18px !important;
            padding: 1.25rem !important;
            margin-top: 1rem !important;
            border: 1px solid #e5e7eb !important;
            box-shadow: 0 8px 24px rgba(0,0,0,0.12) !important;
        }

        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) h1,
        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) h2,
        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) h3,
        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) h4,
        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) p,
        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) li,
        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) span,
        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) label,
        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) div,
        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) [data-testid="stMarkdownContainer"],
        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) [data-testid="stWidgetLabel"] p {
            color: #111111 !important;
        }

        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) .stRadio label span {
            color: #111111 !important;
        }

        div[data-testid="stVerticalBlock"]:has(.course-viewer-anchor) .course-viewer-box {
            background: #ffffff !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin-top: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)


apply_custom_css()

# --- Session State Initialization ---
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "course_pages" not in st.session_state:
    st.session_state.course_pages = []
if "current_page_index" not in st.session_state:
    st.session_state.current_page_index = 0
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "project_ready_to_save" not in st.session_state:
    st.session_state.project_ready_to_save = False
if "draft_loaded" not in st.session_state:
    st.session_state.draft_loaded = False
if "last_saved_course_id" not in st.session_state:
    st.session_state.last_saved_course_id = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Create Course"
if "course_is_public" not in st.session_state:
    st.session_state.course_is_public = False
if "is_read_only" not in st.session_state:
    st.session_state.is_read_only = False

query_params = st.query_params
incoming_access_token = query_params.get("access_token")
incoming_auth_error = query_params.get("auth_error")

if incoming_auth_error:
    st.error(incoming_auth_error)
    st.query_params.clear()

if incoming_access_token and st.session_state.access_token != incoming_access_token:
    st.session_state.access_token = incoming_access_token

    try:
        me_res = requests.get(
            f"{API_URL}/me",
            headers={"Authorization": f"Bearer {incoming_access_token}"},
            timeout=20,
        )
        if me_res.status_code == 200:
            st.session_state.user = me_res.json()
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Login failed while loading your profile.")
    except Exception as e:
        st.error(f"Error completing login: {e}")


def auth_headers():
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def current_display_name():
    if not st.session_state.user:
        return "User"
    return (
        st.session_state.user.get("full_name")
        or st.session_state.user.get("email")
        or "User"
    )

def current_email():
    if not st.session_state.user:
        return ""
    return st.session_state.user.get("email") or ""

def current_initial():
    email = current_email().strip()
    if email:
        return email[0].upper()

    name = current_display_name().strip()
    return name[0].upper() if name else "U"

def get_avatar_data_uri(initial: str) -> str:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
        <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#1f78c1;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#3ca0f0;stop-opacity:1" />
            </linearGradient>
        </defs>
        <circle cx="50" cy="50" r="50" fill="url(#grad1)" />
        <text x="50" y="50" font-family="Arial, sans-serif" font-size="45" font-weight="bold" fill="white" alignment-baseline="central" text-anchor="middle" dy=".1em">{html.escape(initial)}</text>
    </svg>"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"

def render_sidebar_user_card():
    import html
    name = html.escape(current_display_name())
    email = html.escape(current_email())
    initial = html.escape(current_initial())

    return f"""
    <div class="user-card">
        <div class="user-initial">{initial}</div>
        <div class="user-meta">
            <div class="user-name">{name}</div>
            <div class="user-email">{email}</div>
        </div>
    </div>
    """
def is_finish_intent(text: str) -> bool:
    t = text.strip().lower()

    finish_phrases = [
        "the project is done",
        "project is done",
        "i'm done",
        "im done",
        "we are done",
        "we're done",
        "finished",
        "let's save",
        "save the project",
        "save this course",
        "the course is done",
        "done with the project",
        "done with the course",
    ]

    return any(phrase in t for phrase in finish_phrases)


# --- Authentication UI ---
def login():
    st.markdown(
        "<h3 style='text-align: center; color: white; margin-bottom: 0.8rem;'>🔐 Sign in</h3>",
        unsafe_allow_html=True
    )

    st.markdown(
        f'<a class="google-login-link" href="{GOOGLE_LOGIN_URL}" target="_self">Continue with Google</a>',
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='google-note' style='margin-top:1rem; margin-bottom:0.8rem;'>or sign in with email</div>",
        unsafe_allow_html=True
    )

    with st.form("magic_link_form", clear_on_submit=False):
        email = st.text_input(
            "Email",
            placeholder="name@example.com",
            key="magic_link_email"
        )

        submitted = st.form_submit_button("Send magic link ✉️", use_container_width=True)

        if submitted:
            email = email.strip()
            if not email or "@" not in email:
                st.warning("Please enter a valid email address.")
            else:
                try:
                    res = requests.post(
                        f"{API_URL}/auth/email/start",
                        json={"email": email},
                        timeout=20
                    )

                    if res.status_code == 200:
                        st.success("We sent you a sign-in link. Open it from your email on this browser.")
                    else:
                        try:
                            detail = res.json().get("detail", "Failed to send magic link.")
                        except Exception:
                            detail = "Failed to send magic link."
                        st.error(detail)

                except Exception as e:
                    st.error(f"Error connecting to backend: {e}")

# --- Draft Helper Functions ---
def load_draft_state():
    if not st.session_state.access_token:
        return False
    try:
        res = requests.get(f"{API_URL}/chat/draft", headers=auth_headers(), timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data and data.get("messages"):
                st.session_state.messages = data.get("messages", [])
                st.session_state.course_pages = data.get("course_pages", [])
                st.session_state.current_page_index = data.get("current_page_index", 0)
                st.session_state.last_saved_course_id = data.get("last_saved_course_id")
                st.session_state.course_is_public = data.get("course_is_public", False)
                return True
    except:
        pass
    return False

def save_draft_state():
    if not st.session_state.access_token or not st.session_state.messages:
        return
    draft_data = {
        "messages": st.session_state.messages,
        "course_pages": st.session_state.course_pages,
        "current_page_index": st.session_state.current_page_index,
        "last_saved_course_id": st.session_state.last_saved_course_id,
        "course_is_public": st.session_state.course_is_public,
    }
    try:
        requests.post(f"{API_URL}/chat/draft", json=draft_data, headers=auth_headers(), timeout=5)
    except:
        pass

def auto_save_course():
    """Save or update current course pages in My Courses. Uses PUT if a course already exists in this session."""
    if not st.session_state.access_token or not st.session_state.course_pages:
        return None
    auto_title = next(
        (p.get("title", "") for p in st.session_state.course_pages if p.get("type") == "content"),
        "My Course"
    )
    course_content = ""
    for p in st.session_state.course_pages:
        if p.get("type") == "quiz":
            course_content += "### Quiz Questions\n"
            for q in p.get("questions", []):
                course_content += f"- **{q.get('question')}**\n  - Answer: {q.get('correct_answer')}\n  - Explanation: {q.get('explanation')}\n\n"
        else:
            course_content += f"### {p.get('title', '')}\n{p.get('content', '')}\n\n"
    
    # Prepend the full structured data as an invisible HTML comment so Edit can restore it
    json_blob = json.dumps(st.session_state.course_pages, ensure_ascii=False)
    json_header = f"<!-- COURSE_PAGES_JSON\n{json_blob}\n-->\n"

    payload = {"title": auto_title, "content": json_header + course_content, "is_public": st.session_state.course_is_public}
    existing_id = st.session_state.get("last_saved_course_id")
    
    try:
        if existing_id:
            # Update the existing course record
            res = requests.put(
                f"{API_URL}/projects/{existing_id}",
                json=payload,
                headers=auth_headers(), timeout=30
            )
        else:
            # Create brand-new record
            res = requests.post(
                f"{API_URL}/projects",
                json=payload,
                headers=auth_headers(), timeout=30
            )
        if res.status_code == 200:
            saved = res.json()
            st.session_state.last_saved_course_id = saved.get("id", existing_id)
            return saved
    except:
        pass
    return None

# --- UI Components ---
def chat_interface():
    st.title("🎓 Create a New Course")
    st.markdown(
        "Build dynamic micro-lessons and entire courses interactively using our AI platform. "
        "When you're done, just write in the chat that the project/course is finished and then save it."
    )

    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="logo.png"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("user", avatar=get_avatar_data_uri(current_initial())):
                st.markdown(msg["content"])

    user_input = None
    if not st.session_state.get("is_read_only", False):
        user_input = st.chat_input("What topic would you like to build a course about?")
    
    if st.session_state.get("_pending_prompt"):
        prompt = st.session_state.pop("_pending_prompt")
    else:
        prompt = user_input

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar=get_avatar_data_uri(current_initial())):
            st.markdown(prompt)

        if is_finish_intent(prompt):
            st.session_state.project_ready_to_save = True
            assistant_reply = (
                "Great — your project is marked as finished. "
                "Now give it a title below and save it to My Courses."
            )
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            with st.chat_message("assistant"):
                st.markdown(assistant_reply)
            save_draft_state()
        else:
            context = "Previous Chat Messages:\n"
            for m in st.session_state.messages:
                if m["role"] == "assistant":
                    context += m["content"] + "\n"
                    
            context += "\nGenerated Course Content So Far:\n"
            for p in st.session_state.course_pages:
                if p.get("type") == "content":
                    context += f"### {p.get('title')}\n{p.get('content')}\n\n"
                elif p.get("type") == "quiz":
                    context += "### Quiz\n"
                    for q in p.get("questions", []):
                        context += f"- Q: {q.get('question')} (A: {q.get('correct_answer')})\n"

            with st.chat_message("assistant", avatar="logo.png"):
                with st.spinner("Generating your course..."):
                    try:
                        res = requests.post(
                            f"{API_URL}/chat/generate_course",
                            json={"prompt": prompt, "context": context},
                            timeout=60
                        )
                        if res.status_code == 200:
                            data = res.json()
                            chat_message = data.get("chat_message", "Here are your new course pages.")
                            pages = data.get("pages", [])
                            quiz = data.get("quiz", [])
                            
                            num_old_pages = len(st.session_state.course_pages)
                            
                            for p in pages:
                                st.session_state.course_pages.append({"type": "content", "title": p.get("title", ""), "content": p.get("content", "")})
                            
                            if quiz:
                                st.session_state.course_pages.append({"type": "quiz", "questions": quiz})
                                
                            st.session_state.current_page_index = num_old_pages
                                
                            st.markdown(chat_message)
                            st.session_state.messages.append({"role": "assistant", "content": chat_message})
                            save_draft_state()
                            # Auto-save the course
                            saved = auto_save_course()
                            if saved:
                                st.session_state.last_saved_course_id = saved.get("id")
                        else:
                            try:
                                detail = res.json().get("detail", "Failed to generate course.")
                            except Exception:
                                detail = f"Failed to generate course. Status code: {res.status_code}"
                            st.error(detail)
                    except Exception as e:
                        st.error(f"Error: {e}")

     # --- Slide Viewer UI ---
    if st.session_state.course_pages:
        with st.container():
            st.markdown('<div class="course-viewer-anchor"></div>', unsafe_allow_html=True)

            st.subheader("📖 Course Viewer")

            col1, col2, col3 = st.columns([1, 4, 1])

            with col1:
                if st.button(
                    "⬅️ Previous",
                    disabled=st.session_state.current_page_index == 0,
                    use_container_width=True
                ):
                    st.session_state.current_page_index -= 1
                    st.rerun()

            with col3:
                if st.button(
                    "Next ➡️",
                    disabled=st.session_state.current_page_index >= len(st.session_state.course_pages) - 1,
                    use_container_width=True
                ):
                    st.session_state.current_page_index += 1
                    st.rerun()

            with col2:
                st.markdown(
                    f"""
                    <div style='text-align: center; color: #111111; font-weight: 600; padding-top: 5px;'>
                        Page {st.session_state.current_page_index + 1} of {len(st.session_state.course_pages)}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            current_page = st.session_state.course_pages[st.session_state.current_page_index]

            st.markdown("<div class='course-viewer-box'>", unsafe_allow_html=True)

            if current_page.get("type") == "quiz":
                st.markdown(
                    "<div style='color:#111111;'><h3 style='color:#111111;'>📝 Chapter Quiz</h3></div>",
                    unsafe_allow_html=True
                )
                questions = current_page.get("questions", [])

                for i, q in enumerate(questions):
                    st.markdown(
                        f"<div style='color:#111111;'><b>Question {i+1}: {q.get('question', '')}</b></div>",
                        unsafe_allow_html=True
                    )
                    user_ans = st.radio(
                        "Select an answer:",
                        q.get('options', []),
                        key=f"quiz_{st.session_state.current_page_index}_{i}",
                        index=None,
                        label_visibility="collapsed"
                    )

                    check_btn = st.button(
                        "Check Answer",
                        key=f"check_{st.session_state.current_page_index}_{i}"
                    )
                    if check_btn:
                        if user_ans == q.get('correct_answer'):
                            st.success(f"**Correct!** {q.get('explanation', '')}")
                        elif user_ans:
                            st.error(
                                f"**Incorrect.** The correct answer is: {q.get('correct_answer', '')}. {q.get('explanation', '')}"
                            )
                        else:
                            st.warning("Please select an answer first.")
                    st.markdown("---")
            else:
                st.markdown(
                    f"<div style='color:#111111;'><h3 style='color:#111111;'>{current_page.get('title', '')}</h3></div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div style='color:#111111;'>{current_page.get('content', '')}</div>",
                    unsafe_allow_html=True
                )

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")

            if not st.session_state.get("is_read_only", False):
                # Always display the actions below the course content
                st.markdown(
                    "<div style='margin-bottom: 10px; color:#111111;'><b>What would you like to do?</b></div>",
                    unsafe_allow_html=True
                )
                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    if st.button("🔨 Continue Building", use_container_width=True):
                        st.session_state._pending_prompt = "Please continue building the next chapter."
                        # Unshare automatically if they continue building, since it's now a work-in-progress again
                        if st.session_state.course_is_public:
                            st.session_state.course_is_public = False
                            auto_save_course()
                        st.rerun()
                with col_act2:
                    if not st.session_state.course_is_public:
                        if st.button("🌐 Share with Community", use_container_width=True, type="primary"):
                            st.session_state.course_is_public = True
                            saved = auto_save_course()
                            if saved:
                                st.success("🌟 Course published to the community!")
                                st.balloons()
                                save_draft_state()
                                st.rerun()
                            else:
                                st.session_state.course_is_public = False
                                st.error("Failed to publish the course.")
                    else:
                        if st.button("🚫 Unshare", use_container_width=True, type="secondary"):
                            st.session_state.course_is_public = False
                            saved = auto_save_course()
                            if saved:
                                st.success("Course removed from the community.")
                                save_draft_state()
                                st.rerun()
                            else:
                                st.session_state.course_is_public = True
                                st.error("Failed to unshare course.")

                # Show auto-saved info prominently below the actions
                st.info("✅ Course auto-saved to **My Courses**. You can continue adding chapters or start a new course from the sidebar.")


def my_courses_view():
    st.title("📚 My Courses")
    st.markdown("All your saved courses appear here. You can view or delete them at any time.")

    try:
        res = requests.get(
            f"{API_URL}/projects/my",
            headers=auth_headers(),
            timeout=30
        )
        if res.status_code == 200:
            projects = res.json()
            if not projects:
                st.info("You have no saved courses yet.")
                return

            for idx, project in enumerate(projects):
                color = CARD_COLORS[idx % len(CARD_COLORS)]
                visibility_label = "Public" if project.get("is_public") else "Private"
                visibility_icon  = "🌐" if project.get("is_public") else "🔒"
                date_str = (project.get("created_at") or "")[:10]
                content_html = simple_md_to_html(project.get("content", ""))
                title_esc = html.escape(project.get("title", ""))

                col_title, col_edit, col_share, col_del = st.columns([5, 1, 1, 1])
                with col_title:
                    st.markdown(f"""
                        <details style="margin-bottom:0.75rem;border-radius:12px;overflow:hidden;
                                        box-shadow:0 3px 10px rgba(0,0,0,0.15);">
                            <summary style="background:{color};padding:0.85rem 1.2rem;color:white;
                                            font-weight:700;font-size:1rem;cursor:pointer;
                                            list-style:none;border-radius:12px;">
                                {title_esc} &nbsp;&middot;&nbsp; {visibility_icon} {visibility_label}
                            </summary>
                            <div style="background:white;padding:1.25rem 1.5rem;color:#1f2937;
                                        border-radius:0 0 12px 12px;">
                                <p style="color:#6b7280;font-size:0.85rem;margin:0 0 1rem 0;">
                                    Created on: {date_str}
                                </p>
                                {content_html}
                            </div>
                        </details>
                    """, unsafe_allow_html=True)
                with col_edit:
                    if st.button("✏️ Edit", key=f"edit_my_{project['id']}", use_container_width=True):
                        raw_content = project.get("content", "")
                        # Try to restore the original structured pages from the embedded JSON
                        restored_pages = None
                        m = re.search(r'<!-- COURSE_PAGES_JSON\n(.*?)\n-->', raw_content, re.DOTALL)
                        if m:
                            try:
                                restored_pages = json.loads(m.group(1))
                            except Exception:
                                pass
                        if restored_pages:
                            st.session_state.course_pages = restored_pages
                        else:
                            # Fallback for old courses saved before this feature
                            st.session_state.course_pages = [{
                                "type": "content",
                                "title": project.get("title", "My Course"),
                                "content": raw_content,
                            }]
                        st.session_state.current_page_index = 0
                        st.session_state.last_saved_course_id = project["id"]
                        st.session_state.course_is_public = project.get("is_public", False)
                        st.session_state.project_ready_to_save = False
                        st.session_state.is_read_only = False
                        st.session_state.messages = [{
                            "role": "assistant",
                            "content": (
                                f"Welcome back! Continuing course: **{project.get('title', 'My Course')}**.\n\n"
                                "You can ask me to add new chapters, expand existing topics, or make any other changes."
                            ),
                        }]
                        save_draft_state()
                        st.session_state._pending_page = "Create Course"
                        st.rerun()
                with col_share:
                    if not project.get("is_public"):
                        if st.button("🌐 Share", key=f"share_my_{project['id']}", use_container_width=True, type="primary"):
                            share_payload = {
                                "title": project.get("title", ""),
                                "content": project.get("content", ""),
                                "is_public": True
                            }
                            share_res = requests.put(
                                f"{API_URL}/projects/{project['id']}",
                                json=share_payload,
                                headers=auth_headers(),
                                timeout=30
                            )
                            if share_res.status_code == 200:
                                st.success("🌟 Course published to the community!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("Failed to share course.")
                    else:
                        if st.button("🚫 Unshare", key=f"unshare_my_{project['id']}", use_container_width=True, type="secondary"):
                            unshare_payload = {
                                "title": project.get("title", ""),
                                "content": project.get("content", ""),
                                "is_public": False
                            }
                            unshare_res = requests.put(
                                f"{API_URL}/projects/{project['id']}",
                                json=unshare_payload,
                                headers=auth_headers(),
                                timeout=30
                            )
                            if unshare_res.status_code == 200:
                                st.success("Course removed from the community.")
                                st.rerun()
                            else:
                                st.error("Failed to unshare course.")
                with col_del:
                    if st.button("🗑️ Delete", key=f"del_my_{project['id']}", use_container_width=True, type="secondary"):
                        del_res = requests.delete(
                            f"{API_URL}/projects/{project['id']}",
                            headers=auth_headers(),
                            timeout=30
                        )
                        if del_res.status_code == 200:
                            st.success("Course deleted successfully.")
                            st.rerun()
                        else:
                            st.error("Failed to delete course.")
        else:
            st.error("Failed to load your courses.")
    except Exception as e:
        st.error(f"Connection error: {e}")


def shared_courses_view():
    st.title("🌐 Shared Community Courses")
    st.markdown("Explore and learn from courses created by fellow educators and students.")

    try:
        res = requests.get(f"{API_URL}/projects/shared", timeout=30)
        if res.status_code == 200:
            projects = res.json()
            if not projects:
                st.info("No shared courses yet.")
            for idx, project in enumerate(projects):
                color = CARD_COLORS[idx % len(CARD_COLORS)]
                owner_name = (
                    project.get("owner_name")
                    or project.get("owner_email")
                    or "Unknown user"
                )
                date_str = (project.get("created_at") or "")[:10]
                content_html = simple_md_to_html(project.get("content", ""))
                title_esc = html.escape(project.get("title", ""))
                owner_esc = html.escape(str(owner_name))
                col_title, col_start = st.columns([5, 1])
                with col_title:
                    st.markdown(f"""
                        <details style="margin-bottom:0.75rem;border-radius:12px;overflow:hidden;
                                        box-shadow:0 3px 10px rgba(0,0,0,0.15);">
                            <summary style="background:{color};padding:0.85rem 1.2rem;color:white;
                                            font-weight:700;font-size:1rem;cursor:pointer;
                                            list-style:none;border-radius:12px;">
                                {title_esc} &mdash; by {owner_esc}
                            </summary>
                            <div style="background:white;padding:1.25rem 1.5rem;color:#1f2937;
                                        border-radius:0 0 12px 12px;">
                                <p style="color:#6b7280;font-size:0.85rem;margin:0 0 1rem 0;">
                                    Uploaded on: {date_str}
                                </p>
                                {content_html}
                            </div>
                        </details>
                    """, unsafe_allow_html=True)
                with col_start:
                    if st.button("🚀 Start Course", key=f"start_shared_{project['id']}", use_container_width=True, type="primary"):
                        raw_content = project.get("content", "")
                        # Try to restore the original structured pages from the embedded JSON
                        restored_pages = None
                        m = re.search(r'<!-- COURSE_PAGES_JSON\n(.*?)\n-->', raw_content, re.DOTALL)
                        if m:
                            try:
                                restored_pages = json.loads(m.group(1))
                            except Exception:
                                pass
                        if restored_pages:
                            st.session_state.course_pages = restored_pages
                        else:
                            # Fallback for old courses saved before JSON embedding
                            st.session_state.course_pages = [{
                                "type": "content",
                                "title": project.get("title", "Shared Course"),
                                "content": raw_content,
                            }]
                        st.session_state.current_page_index = 0
                        # CRITICAL: leave this None so when the user continues, it saves as a NEW course owned by them!
                        st.session_state.last_saved_course_id = None
                        st.session_state.course_is_public = False
                        st.session_state.project_ready_to_save = False
                        st.session_state.is_read_only = True
                        st.session_state.messages = [{
                            "role": "assistant",
                            "content": (
                                f"Welcome! You are starting **{project.get('title', 'a shared course')}** "
                                f"originally created by {project.get('owner_name') or 'another user'}.\n\n"
                                "You can read the pages, take the quiz, or ask me to modify the course for you. "
                                "Any progress you make will be saved as your own private copy."
                            ),
                        }]
                        save_draft_state()
                        st.session_state._pending_page = "Create Course"
                        st.rerun()
        else:
            st.error("Failed to load courses.")
    except Exception as e:
        st.error(f"Could not connect to backend: {e}")


def admin_panel():
    st.header("Admin Panel")

    if st.session_state.user.get("role") != "admin":
        st.warning("You do not have access to this page.")
        return

    st.subheader("Manage All Courses")
    try:
        res = requests.get(
            f"{API_URL}/admin/projects",
            headers=auth_headers(),
            timeout=30
        )
        if res.status_code == 200:
            projects = res.json()
            if not projects:
                st.info("No courses found in database.")

            for project in projects:
                owner_name = (
                    project.get("owner_name")
                    or project.get("owner_email")
                    or "Unknown user"
                )
                visibility_label = "Public" if project.get("is_public") else "Private"
                visibility_icon  = "🌐" if project.get("is_public") else "🔒"
                date_str = (project.get("created_at") or "")[:10]
                content_html = simple_md_to_html(project.get("content", ""))
                title_esc = html.escape(project.get("title", ""))
                
                # We can just cycle colors based on the project's ID string length or index if we enumerate
                color = CARD_COLORS[len(project['id']) % len(CARD_COLORS)]

                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"""
                        <details style="margin-bottom:0.75rem;border-radius:12px;overflow:hidden;
                                        box-shadow:0 3px 10px rgba(0,0,0,0.15);">
                            <summary style="background:{color};padding:0.85rem 1.2rem;color:white;
                                            font-weight:700;font-size:1rem;cursor:pointer;
                                            list-style:none;border-radius:12px;">
                                {title_esc} by {owner_name} &nbsp;&middot;&nbsp; {visibility_icon} {visibility_label}
                            </summary>
                            <div style="background:white;padding:1.25rem 1.5rem;color:#1f2937;
                                        border-radius:0 0 12px 12px;">
                                <p style="color:#6b7280;font-size:0.85rem;margin:0 0 1rem 0;">
                                    ID: {project['id']} | Created on: {date_str}
                                </p>
                                {content_html}
                            </div>
                        </details>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{project['id']}", use_container_width=True, type="secondary"):
                        del_res = requests.delete(
                            f"{API_URL}/admin/projects/{project['id']}",
                            headers=auth_headers(),
                            timeout=30
                        )
                        if del_res.status_code == 200:
                            st.success("Deleted!")
                            st.rerun()
                        else:
                            st.error("Delete failed.")
        else:
            st.error("Failed to load courses.")
    except Exception as e:
        st.error(f"Could not connect to backend: {e}")


def render_logged_out_page():
    st.markdown("<div class='top-spacer'></div>", unsafe_allow_html=True)

    left, center, right = st.columns([1.15, 1.55, 1.15])

    with center:
        try:
            st.image("logo_without.png", width=340)
        except Exception:
            pass

        st.markdown(
            "<h2 style='text-align: center; color: white; margin-top: 0.4rem; margin-bottom: 0.5rem;'>Welcome to EduBuilder!</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<div class='auth-subtitle'>Sign in with Google or email to build lessons and courses with AI</div>",
            unsafe_allow_html=True
        )
        login()


# --- Main App ---
def main():
    if st.session_state.user is None:
        render_logged_out_page()
        return

    if not st.session_state.draft_loaded:
        st.session_state.draft_loaded = True
        if not st.session_state.messages and load_draft_state():
            st.rerun()

    # Apply any pending programmatic navigation before the radio widget is instantiated
    if st.session_state.get("_pending_page"):
        st.session_state.current_page = st.session_state.pop("_pending_page")

    is_admin = st.session_state.user.get("role") == "admin"

    st.sidebar.markdown("### 🧭 Navigation")
    st.sidebar.markdown(render_sidebar_user_card(), unsafe_allow_html=True)

    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.access_token = None
        st.session_state.messages = []
        st.session_state.current_course = []
        st.session_state.project_ready_to_save = False
        st.rerun()

    if st.sidebar.button("✨ New Course", use_container_width=True, type="primary"):
        # Clear the backend draft so a fresh session starts clean
        try:
            requests.delete(f"{API_URL}/chat/draft", headers=auth_headers(), timeout=5)
        except:
            pass
        st.session_state.messages = []
        st.session_state.course_pages = []
        st.session_state.current_page_index = 0
        st.session_state.last_saved_course_id = None
        st.session_state.course_is_public = False
        st.session_state.project_ready_to_save = False
        st.session_state.is_read_only = False
        st.session_state.current_page = "Create Course"
        st.rerun()

    if is_admin:
        st.sidebar.success("Admin Active")

    pages = ["Create Course", "My Courses", "Shared Courses"]
    if is_admin:
        pages.append("Admin Panel")

    st.sidebar.markdown("### Go to")
    page = st.sidebar.radio("Go to", pages, label_visibility="collapsed", key="current_page")

    if page == "Create Course":
        chat_interface()
    elif page == "My Courses":
        my_courses_view()
    elif page == "Shared Courses":
        shared_courses_view()
    elif page == "Admin Panel":
        admin_panel()


if __name__ == "__main__":
    main()