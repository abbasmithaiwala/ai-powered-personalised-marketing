"""
API endpoints for menu item management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate, MenuItemResponse, MenuItemListResponse
from app.services.menu_service import MenuService

router = APIRouter(prefix="/menu-items")


@router.get("", response_model=MenuItemListResponse)
async def list_menu_items(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    brand_id: Optional[UUID] = Query(None, description="Filter by brand ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine type"),
    dietary_tag: Optional[str] = Query(None, description="Filter by dietary tag"),
    db: AsyncSession = Depends(get_db),
):
    """
    List menu items with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        brand_id: Optional filter by brand ID
        category: Optional filter by category
        cuisine: Optional filter by cuisine type
        dietary_tag: Optional filter by dietary tag
        db: Database session

    Returns:
        Paginated list of menu items
    """
    service = MenuService(db)
    return await service.list_menu_items(
        page=page,
        page_size=page_size,
        brand_id=brand_id,
        category=category,
        cuisine=cuisine,
        dietary_tag=dietary_tag,
    )


@router.post("", response_model=MenuItemResponse, status_code=201)
async def create_menu_item(
    data: MenuItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new menu item.

    Triggers async embedding generation in the background (TASK-010).

    Args:
        data: Menu item creation data
        db: Database session

    Returns:
        Created menu item

    Raises:
        HTTPException: If brand not found or other validation errors
    """
    service = MenuService(db)
    try:
        return await service.create_menu_item(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        if "foreign key" in str(e).lower():
            raise HTTPException(status_code=404, detail="Brand not found")
        raise


@router.get("/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get menu item by ID.

    Args:
        item_id: Menu item UUID
        db: Database session

    Returns:
        Menu item details

    Raises:
        HTTPException: If menu item not found
    """
    service = MenuService(db)
    item = await service.get_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item


@router.put("/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: UUID,
    data: MenuItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing menu item.

    Re-triggers async embedding generation if content changed (TASK-010).

    Args:
        item_id: Menu item UUID
        data: Menu item update data
        db: Database session

    Returns:
        Updated menu item

    Raises:
        HTTPException: If menu item not found
    """
    service = MenuService(db)
    item = await service.update_menu_item(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_menu_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a menu item (set is_available to False).

    Args:
        item_id: Menu item UUID
        db: Database session

    Raises:
        HTTPException: If menu item not found
    """
    service = MenuService(db)
    success = await service.delete_menu_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Menu item not found")
