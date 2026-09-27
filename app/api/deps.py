import secrets

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str | None = Depends(api_key_header)) -> None:
    if key is None or not secrets.compare_digest(key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
