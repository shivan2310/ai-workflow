from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.database import get_db, engine
from app.core.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint reporting API status, database connectivity,
    and cloud LLM configuration status.
    """
    settings = get_settings()

    # Verify DB connectivity
    db_connected = False
    dialect_name = engine.dialect.name
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    llm_configured = bool(settings.LLM_API_KEY and not settings.LLM_API_KEY.startswith("test-"))

    return {
        "status": "healthy" if db_connected else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "connected": db_connected,
            "dialect": dialect_name,
        },
        "llm": {
            "provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL,
            "configured": llm_configured,
        },
    }
