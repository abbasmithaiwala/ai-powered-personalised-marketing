"""
API endpoints for brand management.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.brand import BrandCreate, BrandUpdate, BrandResponse, BrandListResponse
from app.services.menu_service import MenuService

router = APIRouter(prefix="/brands")


@router.get("", response_model=BrandListResponse)
async def list_brands(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all brands with pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session

    Returns:
        Paginated list of brands
    """
    service = MenuService(db)
    return await service.list_brands(page=page, page_size=page_size)


@router.post("", response_model=BrandResponse, status_code=201)
async def create_brand(
    data: BrandCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new brand.

    Args:
        data: Brand creation data
        db: Database session

    Returns:
        Created brand

    Raises:
        HTTPException: If brand with same name already exists
    """
    service = MenuService(db)
    try:
        return await service.create_brand(data)
    except Exception as e:
        # Handle unique constraint violation
        if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail="Brand with this name already exists"
            )
        raise


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get brand by ID.

    Args:
        brand_id: Brand UUID
        db: Database session

    Returns:
        Brand details

    Raises:
        HTTPException: If brand not found
    """
    service = MenuService(db)
    brand = await service.get_brand(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    data: BrandUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing brand.

    Args:
        brand_id: Brand UUID
        data: Brand update data
        db: Database session

    Returns:
        Updated brand

    Raises:
        HTTPException: If brand not found
    """
    service = MenuService(db)
    brand = await service.update_brand(brand_id, data)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.delete("/{brand_id}", status_code=204)
async def delete_brand(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a brand (set is_active to False).

    Args:
        brand_id: Brand UUID
        db: Database session

    Raises:
        HTTPException: If brand not found
    """
    service = MenuService(db)
    success = await service.delete_brand(brand_id)
    if not success:
        raise HTTPException(status_code=404, detail="Brand not found")
