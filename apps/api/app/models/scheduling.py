"""
Scheduling-related Pydantic models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ScheduleTweetRequest(BaseModel):
    """Request model for scheduling a tweet."""

    content: str = Field(..., min_length=1, max_length=25000, description="Tweet content")
    scheduled_for: str = Field(..., description="ISO datetime string for scheduled time")
    analysis: Optional[dict] = Field(None, description="Tweet analysis data")


class ScheduledTweetResponse(BaseModel):
    """Response model for scheduled tweet."""

    id: str
    content: str
    status: str
    scheduled_for: datetime
    created_at: datetime
    analysis: Optional[dict] = None


class UpdateScheduleRequest(BaseModel):
    """Request model for updating scheduled tweet."""

    content: Optional[str] = Field(None, min_length=1, max_length=25000)
    scheduled_for: Optional[str] = Field(None)


class OptimalTimeResponse(BaseModel):
    """Response model for optimal posting times."""

    current: dict = Field(..., description="Current time score")
    best_hours: List[dict] = Field(..., description="Best posting hours")
    recommendation: str = Field(..., description="Time recommendation")
