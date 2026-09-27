from fastapi import Depends, FastAPI

from app.api.deps import require_api_key
from app.api.routes.coins import router as coins_router
from app.api.routes.health import router as health_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version, description=settings.app_description)
app.include_router(health_router, tags=["Health"])
app.include_router(coins_router, tags=["Coins"], dependencies=[Depends(require_api_key)])