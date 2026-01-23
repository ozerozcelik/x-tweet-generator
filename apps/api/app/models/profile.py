"""
Profile-related Pydantic models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProfileCreate(BaseModel):
    """Request model for creating/updating profile."""

    username: Optional[str] = Field(None, max_length=255)
    x_username: Optional[str] = Field(None, max_length=255)
    followers: Optional[int] = Field(0, ge=0)
    verified: Optional[bool] = Field(False)
    following: Optional[int] = Field(0, ge=0)
    total_posts: Optional[int] = Field(0, ge=0)
    avg_like_rate: Optional[float] = Field(0.01, ge=0, le=0.1)
    account_age_years: Optional[float] = Field(1.0, ge=0)


class ProfileResponse(BaseModel):
    """Response model for profile data."""

    id: str
    username: Optional[str] = None
    x_username: Optional[str] = None
    followers: int = 0
    verified: bool = False
    following: int = 0
    total_posts: int = 0
    avg_like_rate: float = 0.01
    account_age_years: float = 1.0
    created_at: datetime
    updated_at: datetime


class StyleAnalysisRequest(BaseModel):
    """Request model for style analysis."""

    tweets: List["TweetData"] = Field(..., min_items=5, description="Tweets to analyze")


class TweetData(BaseModel):
    """Individual tweet data for style analysis."""

    text: str = Field(..., min_length=1)
    likes: Optional[int] = Field(0, ge=0)
    retweets: Optional[int] = Field(0, ge=0)
    replies: Optional[int] = Field(0, ge=0)
    impressions: Optional[int] = Field(100, ge=0)


class StyleAnalysisResponse(BaseModel):
    """Response model for style analysis."""

    avg_length: float = Field(..., description="Average tweet length")
    avg_line_breaks: float = Field(..., description="Average line breaks")
    emoji_frequency: float = Field(..., description="Emojis per tweet")
    question_frequency: float = Field(..., description="Question usage rate")
    hashtag_frequency: float = Field(..., description="Hashtags per tweet")
    mention_frequency: float = Field(..., description="Mentions per tweet")
    tone: str = Field(..., description="Detected tone")
    common_emojis: List[str] = Field(default_factory=list)
    common_words: List[str] = Field(default_factory=list)
    avg_engagement_rate: Optional[float] = None
    style_prompt: str = Field(..., description="AI prompt for this style")


class TweetCredResponse(BaseModel):
    """Response model for TweetCred score."""

    total_score: int = Field(..., description="Total TweetCred score")
    base_score: int = Field(..., description="Base score")
    verified_boost: int = Field(..., description="Verified bonus")
    bio_score: int = Field(..., description="Bio quality score")
    ratio_score: int = Field(..., description="Follower ratio score")
    language_score: int = Field(..., description="Language score")
    engagement_history_score: int = Field(..., description="Engagement history score")
    niche_focus_score: int = Field(..., description="Niche focus score")
    is_positive: bool = Field(..., description="Is score positive?")
    has_cold_start_suppression: bool = Field(..., description="Is cold start suppression active?")
    distribution_rate: float = Field(..., description="Distribution rate (0-1)")


class MonetizationResponse(BaseModel):
    """Response model for monetization analysis."""

    estimated_rpm: float = Field(..., description="Revenue per mille")
    niche_profitability: str = Field(..., description="Niche profitability: low, medium, high")
    target_market: str = Field(..., description="Target market")
    recommended_niches: List[str] = Field(default_factory=list)
    tips: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    monthly_potential: Optional[float] = None


# Update forward references
StyleAnalysisRequest.model_rebuild()
