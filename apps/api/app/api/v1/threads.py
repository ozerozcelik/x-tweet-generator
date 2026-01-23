"""
Thread API routes.
Thread generation and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.deps import SupabaseDep, UserDep, OptionalUserDep
from app.services.thread_generator import get_thread_generator
from app.services.claude import ClaudeService

router = APIRouter()


@router.post("/generate")
async def generate_thread(
    topic: str,
    tweet_count: int = 7,
    style: str = "educational",
    language: str = "tr",
    user_id: OptionalUserDep = None,
    supabase: SupabaseDep = None,
):
    """
    Generate a tweet thread (multiple connected tweets).

    Threads are great for storytelling and educational content.
    """
    generator = get_thread_generator()

    # Get user profile for personalization
    profile_data = None
    if user_id and supabase:
        try:
            profile_result = supabase.table("profiles").select("*").eq("id", user_id).single()
            if profile_result.data:
                profile_data = profile_result.data
        except Exception:
            pass

    # Generate thread
    tweets = await generator.generate_thread(
        topic=topic,
        tweet_count=tweet_count,
        style=style,
        language=language,
        profile=profile_data,
    )

    total_chars = sum(len(t) for t in tweets)

    return {
        "tweets": tweets,
        "total_characters": total_chars,
        "tweet_count": len(tweets),
    }


@router.post("/from-tweet")
async def thread_from_tweet(
    content: str,
    tweet_count: int = 5,
    user_id: OptionalUserDep = None,
    supabase: SupabaseDep = None,
):
    """
    Convert a single long tweet into a thread.

    Useful for breaking down long-form content into multiple tweets.
    """
    generator = get_thread_generator()

    # Get user profile
    profile_data = None
    if user_id and supabase:
        try:
            profile_result = supabase.table("profiles").select("*").eq("id", user_id).single()
            if profile_result.data:
                profile_data = profile_result.data
        except Exception:
            pass

    # Generate thread from content
    tweets = await generator.expand_to_thread(
        content=content,
        tweet_count=tweet_count,
        profile=profile_data,
    )

    return {
        "tweets": tweets,
        "total_characters": sum(len(t) for t in tweets),
        "tweet_count": len(tweets),
    }


@router.get("/templates")
async def get_thread_templates():
    """Get available thread starter templates."""
    generator = get_thread_generator()
    return generator.get_thread_templates()
