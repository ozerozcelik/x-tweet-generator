"""
Profile API routes.
User profile management, style analysis, TweetCred, and monetization.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.deps import SupabaseDep, UserDep
from app.models.profile import (
    ProfileCreate,
    ProfileResponse,
    StyleAnalysisRequest,
    StyleAnalysisResponse,
    TweetCredResponse,
    MonetizationResponse,
)
from app.services.analyzer import (
    TweetStyleAnalyzer,
    TweetCredAnalyzer,
    MonetizationAnalyzer,
)

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """Get current user's profile."""
    try:
        result = supabase.table("profiles") \
            .select("*") \
            .eq("id", user_id) \
            .single() \
            .execute()

        if not result.data:
            # Create default profile
            profile_data = {
                "id": user_id,
                "followers": 0,
                "verified": False,
                "following": 0,
                "total_posts": 0,
                "avg_like_rate": 0.01,
            }
            supabase.table("profiles").insert(profile_data).execute()
            return ProfileResponse(**profile_data, created_at=None, updated_at=None)

        return result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )


@router.post("/me")
async def update_profile(
    profile: ProfileCreate,
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """Update current user's profile."""
    try:
        # Check if profile exists
        existing = supabase.table("profiles") \
            .select("*") \
            .eq("id", user_id) \
            .single() \
            .execute()

        update_data = profile.model_dump(exclude_unset=True)

        if existing.data:
            # Update existing
            result = supabase.table("profiles") \
                .update(update_data) \
                .eq("id", user_id) \
                .select("*") \
                .single() \
                .execute()
        else:
            # Create new
            result = supabase.table("profiles") \
                .insert({**update_data, "id": user_id}) \
                .select("*") \
                .single() \
                .execute()

        return result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.post("/analyze-style", response_model=StyleAnalysisResponse)
async def analyze_style(
    request: StyleAnalysisRequest,
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """
    Analyze user's tweet writing style.

    Returns metrics about writing patterns and generates an AI prompt
    that matches their style.
    """
    analyzer = TweetStyleAnalyzer()

    # Convert request format
    tweets = [
        {
            "text": t.text,
            "likes": t.likes or 0,
            "retweets": t.retweets or 0,
            "replies": t.replies or 0,
            "impressions": t.impressions or 100,
        }
        for t in request.tweets
    ]

    analysis = analyzer.analyze_tweets(tweets)

    # Save analysis to database
    try:
        supabase.table("style_analyses").insert({
            "user_id": user_id,
            "analysis_data": analysis.model_dump(),
        }).execute()
    except Exception:
        pass  # Don't fail if save fails

    return analysis


@router.get("/tweetcred", response_model=TweetCredResponse)
async def get_tweetcred(
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """
    Get user's TweetCred score.

    TweetCred is X's internal authority scoring system.
    """
    # Get profile
    profile_result = supabase.table("profiles") \
        .select("*") \
        .eq("id", user_id) \
        .single() \
        .execute()

    if not profile_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    profile = profile_result.data

    # Calculate TweetCred
    analyzer = TweetCredAnalyzer()
    score = analyzer.calculate_tweetcred(
        followers=profile.get("followers", 0),
        verified=profile.get("verified", False),
        following=profile.get("following", 0),
        account_age_days=profile.get("account_age_years", 1) * 365,
        avg_engagement_rate=profile.get("avg_like_rate", 0.01),
    )

    return score


@router.get("/monetization", response_model=MonetizationResponse)
async def get_monetization(
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """
    Get monetization analysis.

    Estimates potential revenue from X ad revenue sharing.
    """
    # Get profile
    profile_result = supabase.table("profiles") \
        .select("*") \
        .eq("id", user_id) \
        .single() \
        .execute()

    if not profile_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    profile = profile_result.data

    # Analyze monetization
    analyzer = MonetizationAnalyzer()
    analysis = analyzer.get_monetization_analysis(
        followers=profile.get("followers", 0),
        country="TR",  # Default, should be in profile
        niche="genel",  # Default, should be in profile
        avg_engagement_rate=profile.get("avg_like_rate", 0.01),
    )

    return analysis
