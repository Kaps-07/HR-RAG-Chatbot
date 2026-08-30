"""
main.py - FastAPI app for HR Assistant RAG Chatbot
Adds session-based authentication and role-based access control
on top of the existing RAG / document-management functionality.
"""

import os
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from config import UPLOAD_FOLDER, INDEX_STORE
from rag.vectorstore import allowed_file, add_file_to_index, delete_file_from_index, vectorstore
from rag.pipeline import rag_search
from authentication import register_user, login_user

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(INDEX_STORE, exist_ok=True)

# ---------------------------------------------------------------------------
# App + middleware
# ---------------------------------------------------------------------------

app = FastAPI()

# SessionMiddleware signs the cookie with the secret key using itsdangerous,
# so the client cannot tamper with session data.
# Change the secret_key to a long random string before deploying.
app.add_middleware(
    SessionMiddleware,
    secret_key="hr-assistant-secret-change-me",
    session_cookie="hr_session",
    max_age=3600,        # session expires after 1 hour of inactivity
    https_only=False,    # set True when running on HTTPS
    same_site="lax",
)

templates = Jinja2Templates(directory="templates")

# Mount static files only if the folder exists (graceful for fresh checkouts)
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


# ---------------------------------------------------------------------------
# Auth helper functions
# ---------------------------------------------------------------------------

def get_current_user(request: Request):
    """Return the session user dict {email, role} or None if not logged in."""
    return request.session.get("user")


def redirect_if_not_logged_in(request: Request):
    """Return a RedirectResponse to /login if there is no active session."""
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=302)
    return None


def require_hr(request: Request):
    """
    Return an error response if the caller is not a logged-in HR user.
    Used for both page routes (returns HTML 403) and API routes (returns JSON 403).
    Returns None when the user IS a valid HR user, so the route can continue.
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.get("role") != "hr":
        # Determine whether the caller expects JSON (API) or HTML (page)
        accept = request.headers.get("accept", "")
        if "application/json" in accept or "text/html" not in accept:
            return JSONResponse({"error": "Access denied. HR role required."}, status_code=403)
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html><head><title>Access Denied</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
            <style>
                *{box-sizing:border-box;margin:0;padding:0}
                body{font-family:'Inter',sans-serif;display:flex;align-items:center;
                     justify-content:center;min-height:100vh;background:#f1f5f9}
                .box{background:#fff;border-radius:14px;padding:48px 40px;
                     box-shadow:0 4px 24px rgba(0,0,0,.10);text-align:center;max-width:400px}
                h2{color:#dc2626;margin-bottom:12px;font-size:1.4rem}
                p{color:#64748b;margin-bottom:28px;line-height:1.6}
                a{display:inline-block;padding:10px 28px;background:#1e40af;
                  color:#fff;border-radius:8px;text-decoration:none;font-weight:600}
            </style></head>
            <body><div class="box">
                <h2>&#128683; Access Denied</h2>
                <p>You do not have permission to view this page.<br>
                   This area is restricted to HR users only.</p>
                <a href="/chatbot">Back to Chatbot</a>
            </div></body></html>""",
            status_code=403,
        )
    return None   # all good — let the route continue


# ---------------------------------------------------------------------------
# Startup: index any uploaded files not yet in the vector store
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_load():
    """Index any existing files in UPLOAD_FOLDER not yet in the vectorstore."""
    existing = vectorstore.get()
    indexed_files = {m["filename"] for m in existing["metadatas"]} if existing["metadatas"] else set()
    for fname in os.listdir(UPLOAD_FOLDER):
        if fname.endswith(".txt") and fname not in indexed_files:
            with open(os.path.join(UPLOAD_FOLDER, fname), "r", encoding="utf-8") as f:
                add_file_to_index(fname, f.read())


# ---------------------------------------------------------------------------
# Authentication routes
# ---------------------------------------------------------------------------

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # Already logged in — send to the right place
    user = get_current_user(request)
    if user:
        return RedirectResponse(
            url="/dashboard" if user["role"] == "hr" else "/chatbot",
            status_code=302,
        )
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    success, result = login_user(email, password)
    if not success:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": result},
            status_code=401,
        )
    # Store only safe fields in the session — never the password hash
    request.session["user"] = {"email": result["email"], "role": result["role"]}
    if result["role"] == "hr":
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/chatbot", status_code=302)


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(
            url="/dashboard" if user["role"] == "hr" else "/chatbot",
            status_code=302,
        )
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
):
    success, message = register_user(email, password, role)
    if not success:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": message},
            status_code=400,
        )
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "success": message},
    )


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user["role"] == "hr":
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/chatbot", status_code=302)


# ---------------------------------------------------------------------------
# HR Dashboard  (HR only)
# ---------------------------------------------------------------------------

@app.get("/dashboard", response_class=HTMLResponse)
async def hr_dashboard(request: Request):
    guard = require_hr(request)
    if guard:
        return guard
    return templates.TemplateResponse(
        "hr_dashboard.html",
        {"request": request, "user": get_current_user(request)},
    )


# ---------------------------------------------------------------------------
# Chatbot page  (any logged-in user)
# ---------------------------------------------------------------------------

@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request):
    guard = redirect_if_not_logged_in(request)
    if guard:
        return guard
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user": get_current_user(request)},
    )


# ---------------------------------------------------------------------------
# Document management page  (HR only)
# ---------------------------------------------------------------------------

@app.get("/manage", response_class=HTMLResponse)
async def manage(request: Request):
    guard = require_hr(request)
    if guard:
        return guard
    return templates.TemplateResponse(
        "manage.html",
        {"request": request, "user": get_current_user(request)},
    )


# ---------------------------------------------------------------------------
# API — list files  (HR only)
# ---------------------------------------------------------------------------

@app.get("/list_files")
async def list_files(request: Request):
    guard = require_hr(request)
    if guard:
        return guard
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".txt")]
    return {"files": files}


# ---------------------------------------------------------------------------
# API — upload files  (HR only)
# ---------------------------------------------------------------------------

@app.post("/upload")
async def upload_files(
    request: Request,
    files: list[UploadFile] = File(..., alias="files[]"),
):
    guard = require_hr(request)
    if guard:
        return guard
    uploaded = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = os.path.basename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            content = await file.read()
            with open(filepath, "wb") as f:
                f.write(content)
            add_file_to_index(filename, content.decode("utf-8"))
            uploaded.append(filename)
    return {"uploaded": uploaded, "message": f"Uploaded {len(uploaded)} files. Index updated."}


# ---------------------------------------------------------------------------
# API — delete file  (HR only)
# ---------------------------------------------------------------------------

@app.post("/delete_file")
async def delete_file(request: Request):
    guard = require_hr(request)
    if guard:
        return guard
    data = await request.json()
    filename = data.get("filename")
    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    os.remove(path)
    delete_file_from_index(filename)
    return {"deleted": filename, "message": "File deleted and index updated."}


# ---------------------------------------------------------------------------
# API — RAG search  (any logged-in user)
# ---------------------------------------------------------------------------

@app.post("/search")
async def search(request: Request):
    guard = redirect_if_not_logged_in(request)
    if guard:
        return JSONResponse({"error": "Please log in to use the chatbot."}, status_code=401)
    data = await request.json()
    query = data.get("query", "")
    k = int(data.get("top_k", 3))
    history = data.get("history", [])
    resp, code = rag_search(query, k, history)
    return JSONResponse(resp, status_code=code)


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
