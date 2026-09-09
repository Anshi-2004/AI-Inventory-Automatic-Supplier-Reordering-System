"""
FastAPI application factory and startup lifecycle.
Updated database configuration for SQLite fallback.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.routes import auth, products, suppliers, inventory, alerts, purchase_orders, ai_email, email_logs, dashboard
from app.scheduler.scheduler_setup import start_scheduler, stop_scheduler
from app.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)

    # Start background scheduler
    start_scheduler()

    yield  # ← Application runs here

    # Shutdown
    stop_scheduler()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-Based Smart Inventory & Automated Supplier Reordering System. "
        "Monitors stock levels, detects low/critical/emergency conditions, "
        "generates AI supplier emails via LangChain + OpenRouter, "
        "and implements human-in-the-loop email approval."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(suppliers.router)
app.include_router(inventory.router)
app.include_router(alerts.router)
app.include_router(purchase_orders.router)
app.include_router(ai_email.router)
app.include_router(email_logs.router)
app.include_router(dashboard.router)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "1.0.0",
        "env": settings.app_env,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.backend_port, reload=True)
