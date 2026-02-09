"""Customer preference schemas"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Optional


class BrandAffinityItem(BaseModel):
    """Brand affinity item"""
    brand_id: str
    brand_name: str
    score: float


class CustomerPreferenceResponse(BaseModel):
    """Response schema for customer preferences"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    favorite_cuisines: Optional[Dict[str, float]] = None
    favorite_categories: Optional[Dict[str, float]] = None
    dietary_flags: Optional[Dict[str, bool]] = None
    price_sensitivity: Optional[str] = None
    order_frequency: Optional[str] = None
    brand_affinity: Optional[List[Dict]] = None
    preferred_order_times: Optional[Dict[str, float]] = None
    last_computed_at: Optional[datetime] = None
    version: int
    created_at: datetime
    updated_at: datetime
