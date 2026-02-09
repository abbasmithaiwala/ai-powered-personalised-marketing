"""Customer API endpoints"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.intelligence import PreferenceEngine
from app.schemas.customer_preference import CustomerPreferenceResponse

router = APIRouter()


@router.post("/{customer_id}/recompute-preferences", response_model=CustomerPreferenceResponse)
async def recompute_customer_preferences(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Recompute preference signals for a specific customer based on their order history.

    This endpoint analyzes the customer's full order history and updates:
    - Favorite cuisines (with recency weighting)
    - Favorite categories
    - Dietary flags
    - Price sensitivity
    - Order frequency
    - Brand affinity
    - Preferred order times
    """
    try:
        engine = PreferenceEngine(db)
        preference = await engine.compute_preferences(customer_id)

        return CustomerPreferenceResponse.model_validate(preference)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute preferences: {str(e)}")
