from fastapi import Request
from fastapi.responses import RedirectResponse
from functools import wraps

ADMIN_USERNAME = "sebastijan"
ADMIN_PASSWORD = "admin123"

def verify_credentials(username: str, password: str) -> bool:
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def login_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if not request.session.get("user"):
            return RedirectResponse("/login", status_code=302)
        return await func(request, *args, **kwargs)
    return wrapper

