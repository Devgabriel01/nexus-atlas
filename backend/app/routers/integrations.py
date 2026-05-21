"""
Status of all external integrations — Mapbox, Groq, Earth Engine, etc.
Used by the dashboard to show which subsystems are online.
"""
from fastapi import APIRouter
from typing import Dict, Any
from app.config import get_settings
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/integrations", tags=["Integrations"])

settings = get_settings()


@router.get("/status")
async def integrations_status() -> Dict[str, Any]:
    """Returns the status of every external integration the platform uses."""
    return {
        "mapbox": _mapbox_status(),
        "groq": _groq_status(),
        "earth_engine": _gee_status(),
        "openai": {"configured": bool(settings.OPENAI_API_KEY), "active": False},
    }


def _mapbox_status() -> Dict[str, Any]:
    token = settings.MAPBOX_TOKEN or ""
    return {
        "configured": token.startswith("pk."),
        "provider": "mapbox",
        "note": "Token lives in frontend/.env (VITE_MAPBOX_TOKEN)",
    }


def _groq_status() -> Dict[str, Any]:
    return get_ai_service().status


def _gee_status() -> Dict[str, Any]:
    project = settings.GEE_PROJECT
    if not project:
        return {"configured": False, "provider": "earth_engine", "project": None,
                "error": "GEE_PROJECT not set"}
    # Lightweight check: ee module available + credentials cached
    try:
        import ee  # noqa: F401
        import os
        creds = os.path.expanduser("~/.config/earthengine/credentials")
        creds_alt = os.path.expanduser("~/.earthengine/credentials")
        has_creds = os.path.exists(creds) or os.path.exists(creds_alt)
        return {
            "configured": has_creds,
            "provider": "earth_engine",
            "project": project,
            "auth_mode": "user_oauth",
            "error": None if has_creds else "credentials not found — run `earthengine authenticate`",
        }
    except ImportError:
        return {"configured": False, "provider": "earth_engine", "project": project,
                "error": "earthengine-api package not installed"}
