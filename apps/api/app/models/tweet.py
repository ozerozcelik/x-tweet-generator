"""
Tweet-related Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TweetGenerateRequest(BaseModel):
    """Request model for tweet generation."""

    topic: str = Field(..., min_length=1, max_length=500, description="Tweet topic")
    style: Optional[str] = Field(
        "casual",
        description="Tweet style: professional, casual, provocative, storytelling, educational"
    )
    tone: Optional[str] = Field(
        "engaging",
        description="Tweet tone: engaging, controversial, inspirational, humorous, raw"
    )
    length: Optional[str] = Field(
        "medium",
        description="Tweet length: short, medium, long, epic"
    )
    language: Optional[str] = Field(
        "tr",
        description="Language code: tr, en, de, fr, es, ar, zh, ja, ko, pt, ru"
    )
    include_cta: Optional[bool] = Field(True, description="Include call to action")
    include_emoji: Optional[bool] = Field(True, description="Include emojis")
    custom_instructions: Optional[str] = Field(None, max_length=1000)


class TweetAnalysisRequest(BaseModel):
    """Request model for tweet analysis."""

    content: str = Field(..., min_length=1, max_length=25000, description="Tweet content")
    include_predictions: Optional[bool] = Field(True, description="Include engagement predictions")


class TweetOptimizeRequest(BaseModel):
    """Request model for tweet optimization."""

    content: str = Field(..., min_length=1, max_length=25000, description="Tweet to optimize")
    target_score: Optional[int] = Field(80, ge=0, le=100, description="Target algorithm score")


class TweetRewriteRequest(BaseModel):
    """Request model for tweet rewriting."""

    content: str = Field(..., min_length=1, max_length=25000, description="Tweet to rewrite")
    style: str = Field(..., description="Target style: viral, controversial, emotional, educational")


class TweetGenerateResponse(BaseModel):
    """Response model for tweet generation."""

    content: str = Field(..., description="Generated tweet content")
    analysis: Optional["TweetAnalysisResponse"] = None
    character_count: int = Field(..., description="Tweet character count")


class TweetAnalysisResponse(BaseModel):
    """Response model for tweet analysis."""

    score: float = Field(..., ge=0, le=100, description="Algorithm score (0-100)")
    strengths: List[str] = Field(default_factory=list, description="Strong points")
    weaknesses: List[str] = Field(default_factory=list, description="Weak points")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    engagement_prediction: Optional["EngagementPrediction"] = None
    profile_boost: float = Field(1.0, description="Profile-based multiplier")


class EngagementPrediction(BaseModel):
    """Engagement prediction model."""

    favorite: float = Field(..., description="Like probability")
    reply: float = Field(..., description="Reply probability")
    repost: float = Field(..., description="Retweet probability")
    quote: float = Field(..., description="Quote tweet probability")
    follow_author: float = Field(..., description="Follow probability")


class ThreadGenerateRequest(BaseModel):
    """Request model for thread generation."""

    topic: str = Field(..., min_length=1, max_length=500, description="Thread topic")
    tweet_count: Optional[int] = Field(7, ge=3, le=15, description="Number of tweets")
    style: Optional[str] = Field("educational", description="Thread style")
    language: Optional[str] = Field("tr", description="Language code")


class ThreadGenerateResponse(BaseModel):
    """Response model for thread generation."""

    tweets: List[str] = Field(..., description="Thread tweets")
    total_characters: int = Field(..., description="Total character count")


# Update forward references
TweetGenerateResponse.model_rebuild()
