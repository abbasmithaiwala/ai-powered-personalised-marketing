"""Recommendation API endpoints"""

from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.intelligence import RecommendationEngine
from app.schemas.recommendation import RecommendationsResponse

router = APIRouter()


@router.get("/{customer_id}/recommendations", response_model=RecommendationsResponse)
async def get_customer_recommendations(
    customer_id: UUID,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate personalized menu item recommendations for a customer.

    This endpoint uses the customer's taste profile vector and preference signals
    to recommend items they are likely to enjoy. The recommendation strategy:

    1. Fetches the customer's taste profile vector from Qdrant
    2. Searches menu item embeddings by cosine similarity
    3. Filters results:
       - Excludes items ordered in the last 30 days
       - Excludes items violating dietary restrictions (e.g., no non-veg for vegetarians)
       - Includes at least one item from a brand the customer hasn't tried
    4. Returns top N items with scores and human-readable reasons

    **Fallback behavior**: If no taste profile exists, returns popular/trending items
    while still respecting dietary restrictions.

    **Performance**: Response generated in under 1 second.
    """
    try:
        engine = RecommendationEngine(db)
        recommendations, fallback_used = await engine.generate_recommendations(
            customer_id=customer_id,
            limit=limit,
            exclude_recent_days=30,
        )

        return RecommendationsResponse(
            customer_id=customer_id,
            items=recommendations,
            computed_at=datetime.now(timezone.utc),
            fallback_used=fallback_used,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate recommendations: {str(e)}"
        )
