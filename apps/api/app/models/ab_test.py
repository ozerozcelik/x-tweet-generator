"""
A/B Testing related Pydantic models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AbCampaignCreate(BaseModel):
    """Request model for creating A/B test campaign."""

    name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    variants: List[str] = Field(..., min_items=2, max_items=5, description="Tweet variants")


class AbCampaignResponse(BaseModel):
    """Response model for A/B campaign."""

    id: str
    name: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class AbVariantResponse(BaseModel):
    """Response model for A/B test variant."""

    id: str
    campaign_id: str
    content: str
    is_winner: bool
    impressions: int = 0
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    created_at: datetime


class AbResultsResponse(BaseModel):
    """Response model for A/B test results."""

    campaign_id: str
    campaign_name: str
    status: str
    variants: List[AbVariantResponse]
    winner: Optional[AbVariantResponse] = None
    statistical_significance: Optional[float] = None


class SetWinnerRequest(BaseModel):
    """Request model for setting A/B test winner."""

    variant_id: str = Field(..., description="Winning variant ID")
