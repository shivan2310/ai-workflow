import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.api.routes import health, workflows, tasks
from app.db.database import create_all_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autopilot")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    # For dev/test SQLite environments, ensure tables exist
    if settings.DATABASE_URL.startswith("sqlite"):
        create_all_tables()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Account-based Agentic AI Workflow Automation Backend with deterministic verification.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Request validation failed",
            "status_code": 422,
            "detail": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception during {request.method} {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "An internal server error occurred.",
            "status_code": 500,
        },
    )


# Include API Routers under /api
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(workflows.router, prefix=settings.API_PREFIX)
app.include_router(tasks.router, prefix=settings.API_PREFIX)
