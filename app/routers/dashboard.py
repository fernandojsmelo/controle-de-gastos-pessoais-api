from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

DASHBOARD_HTML_PATH = Path(__file__).resolve().parent.parent / "static" / "dashboard.html"


@router.get("/", include_in_schema=False)
@router.get("/dashboard", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(DASHBOARD_HTML_PATH, media_type="text/html")
