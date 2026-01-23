"""
Tweet API routes.
Generation, analysis, optimization, and rewriting.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.deps import SupabaseDep, UserDep, OptionalUserDep
from app.models.tweet import (
    TweetGenerateRequest,
    TweetGenerateResponse,
    TweetAnalysisRequest,
    TweetAnalysisResponse,
    TweetOptimizeRequest,
    TweetRewriteRequest,
)
from app.services.analyzer import TweetAnalyzer
from app.services.claude import ClaudeService

router = APIRouter()


@router.post("/generate", response_model=TweetGenerateResponse)
async def generate_tweet(
    request: TweetGenerateRequest,
    supabase: SupabaseDep,
    user_id: OptionalUserDep = None,
):
    """
    Generate a tweet using AI.

    Requires optional authentication for personalized results.
    """
    claude_service = ClaudeService()

    # Get user profile if authenticated
    profile_data = None
    if user_id:
        try:
            profile_result = supabase.table("profiles").select("*").eq("id", user_id).single()
            if profile_result.data:
                profile_data = profile_result.data
        except Exception:
            pass

    # Generate tweet
    content = await claude_service.generate_tweet(
        topic=request.topic,
        style=request.style,
        tone=request.tone,
        length=request.length,
        language=request.language,
        include_cta=request.include_cta,
        include_emoji=request.include_emoji,
        custom_instructions=request.custom_instructions,
        profile=profile_data,
    )

    # Analyze the generated tweet
    analyzer = TweetAnalyzer()
    analysis = analyzer.analyze(content, profile_data)

    # Save to database if authenticated
    if user_id:
        try:
            supabase.table("tweets").insert({
                "user_id": user_id,
                "content": content,
                "analysis": analysis.model_dump(),
                "status": "draft",
            }).execute()
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to save tweet: {e}")

    return TweetGenerateResponse(
        content=content,
        analysis=analysis,
        character_count=len(content),
    )


@router.post("/analyze", response_model=TweetAnalysisResponse)
async def analyze_tweet(
    request: TweetAnalysisRequest,
    user_id: OptionalUserDep = None,
    supabase: SupabaseDep = None,
):
    """
    Analyze a tweet using X's algorithm scoring system.

    Returns Phoenix score, engagement predictions, and suggestions.
    """
    analyzer = TweetAnalyzer()

    # Get user profile if available for personalized analysis
    profile_data = None
    if user_id and supabase:
        try:
            profile_result = supabase.table("profiles").select("*").eq("id", user_id).single()
            if profile_result.data:
                profile_data = profile_result.data
        except Exception:
            pass

    analysis = analyzer.analyze(request.content, profile_data)

    return analysis


@router.post("/optimize", response_model=TweetGenerateResponse)
async def optimize_tweet(
    request: TweetOptimizeRequest,
    user_id: OptionalUserDep = None,
    supabase: SupabaseDep = None,
):
    """
    Optimize a tweet to improve its algorithm score.

    Uses AI to rewrite the tweet while maintaining the original message.
    """
    analyzer = TweetAnalyzer()

    # Get user profile
    profile_data = None
    if user_id and supabase:
        try:
            profile_result = supabase.table("profiles").select("*").eq("id", user_id).single()
            if profile_result.data:
                profile_data = profile_result.data
        except Exception:
            pass

    # Analyze original
    original_analysis = analyzer.analyze(request.content, profile_data)

    # If already at target score, return original
    if original_analysis.score >= request.target_score:
        return TweetGenerateResponse(
            content=request.content,
            analysis=original_analysis,
            character_count=len(request.content),
        )

    # Optimize using AI
    claude_service = ClaudeService()
    optimized = await claude_service.optimize_tweet(
        content=request.content,
        target_score=request.target_score,
        original_analysis=original_analysis,
        profile=profile_data,
    )

    # Analyze optimized version
    optimized_analysis = analyzer.analyze(optimized, profile_data)

    return TweetGenerateResponse(
        content=optimized,
        analysis=optimized_analysis,
        character_count=len(optimized),
    )


@router.post("/rewrite", response_model=TweetGenerateResponse)
async def rewrite_tweet(
    request: TweetRewriteRequest,
    user_id: OptionalUserDep = None,
    supabase: SupabaseDep = None,
):
    """
    Rewrite a tweet in a different style.

    Supported styles: viral, controversial, emotional, educational.
    """
    claude_service = ClaudeService()
    analyzer = TweetAnalyzer()

    # Get user profile
    profile_data = None
    if user_id and supabase:
        try:
            profile_result = supabase.table("profiles").select("*").eq("id", user_id).single()
            if profile_result.data:
                profile_data = profile_result.data
        except Exception:
            pass

    # Rewrite using AI
    rewritten = await claude_service.rewrite_tweet(
        content=request.content,
        style=request.style,
        profile=profile_data,
    )

    # Analyze rewritten version
    analysis = analyzer.analyze(rewritten, profile_data)

    return TweetGenerateResponse(
        content=rewritten,
        analysis=analysis,
        character_count=len(rewritten),
    )


@router.get("/")
async def get_tweets(
    user_id: UserDep,
    supabase: SupabaseDep,
    limit: int = 50,
    offset: int = 0,
):
    """Get user's saved tweets."""
    try:
        result = supabase.table("tweets") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()

        return result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tweets: {str(e)}"
        )


@router.get("/{tweet_id}")
async def get_tweet(
    tweet_id: str,
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """Get a specific tweet by ID."""
    try:
        result = supabase.table("tweets") \
            .select("*") \
            .eq("id", tweet_id) \
            .eq("user_id", user_id) \
            .single() \
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tweet not found"
            )

        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tweet: {str(e)}"
        )
