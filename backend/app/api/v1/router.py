from fastapi import APIRouter
from app.api.v1.endpoints import health, ingestion, brands, menu_items, customers, admin, recommendations, campaigns

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(ingestion.router, tags=["ingestion"])
router.include_router(brands.router, tags=["brands"])
router.include_router(menu_items.router, tags=["menu-items"])
router.include_router(customers.router, prefix="/customers", tags=["customers"])
router.include_router(recommendations.router, prefix="/customers", tags=["recommendations"])
router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
router.include_router(admin.router, tags=["admin"])
