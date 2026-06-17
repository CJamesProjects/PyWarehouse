from fastapi import FastAPI
from src.api import products
from src.utils.config import settings
from src.utils.database import check_connection

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
)

app.include_router(products.router)


@app.get("/")
def root():
    return {"name": settings.app_title, "version": settings.app_version}


@app.get("/health")
def health():
    """Simple health check - confirms the API is up and can reach the database."""
    db_ok = check_connection()
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}