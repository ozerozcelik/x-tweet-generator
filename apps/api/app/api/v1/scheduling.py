"""
Scheduling API routes.
Tweet scheduling and optimal time recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from typing import List
import pytz

from app.core.deps import SupabaseDep, UserDep
from app.models.scheduling import (
    ScheduleTweetRequest,
    ScheduledTweetResponse,
    OptimalTimeResponse,
)
from app.services.scheduler import TweetScheduler

router = APIRouter()

# Initialize scheduler
tweet_scheduler = TweetScheduler()


@router.post("/schedule", response_model=ScheduledTweetResponse)
async def schedule_tweet(
    request: ScheduleTweetRequest,
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """
    Schedule a tweet for automatic posting.

    The tweet will be posted automatically at the scheduled time
    if X API credentials are configured.
    """
    try:
        # Parse and validate scheduled time
        scheduled_for = datetime.fromisoformat(request.scheduled_for.replace('Z', '+00:00'))

        # Don't allow scheduling in the past
        if scheduled_for < datetime.now(pytz.UTC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot schedule tweets in the past"
            )

        # Insert into database
        result = supabase.table("tweets").insert({
            "user_id": user_id,
            "content": request.content,
            "analysis": request.analysis,
            "status": "scheduled",
            "scheduled_for": scheduled_for.isoformat(),
        }).select("*").single().execute()

        return result.data

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid datetime format. Use ISO 8601 format."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule tweet: {str(e)}"
        )


@router.get("/upcoming")
async def get_upcoming_tweets(
    user_id: UserDep,
    supabase: SupabaseDep,
    limit: int = 10,
):
    """Get user's upcoming scheduled tweets."""
    try:
        now = datetime.now(pytz.UTC).isoformat()

        result = supabase.table("tweets") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("status", "scheduled") \
            .gte("scheduled_for", now) \
            .order("scheduled_for", desc=False) \
            .limit(limit) \
            .execute()

        return result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scheduled tweets: {str(e)}"
        )


@router.put("/{tweet_id}")
async def update_scheduled_tweet(
    tweet_id: str,
    content: str | None = None,
    scheduled_for: str | None = None,
    user_id: UserDep = None,
    supabase: SupabaseDep = None,
):
    """Update a scheduled tweet."""
    try:
        update_data = {}
        if content:
            update_data["content"] = content
        if scheduled_for:
            scheduled_datetime = datetime.fromisoformat(scheduled_for.replace('Z', '+00:00'))
            if scheduled_datetime < datetime.now(pytz.UTC):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot schedule tweets in the past"
                )
            update_data["scheduled_for"] = scheduled_datetime

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided"
            )

        result = supabase.table("tweets") \
            .update(update_data) \
            .eq("id", tweet_id) \
            .eq("user_id", user_id) \
            .eq("status", "scheduled") \
            .select("*") \
            .single() \
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled tweet not found"
            )

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scheduled tweet: {str(e)}"
        )


@router.delete("/{tweet_id}")
async def delete_scheduled_tweet(
    tweet_id: str,
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """Delete a scheduled tweet."""
    try:
        result = supabase.table("tweets") \
            .delete() \
            .eq("id", tweet_id) \
            .eq("user_id", user_id) \
            .eq("status", "scheduled") \
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled tweet not found"
            )

        return {"message": "Tweet deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scheduled tweet: {str(e)}"
        )


@router.get("/optimal-times", response_model=OptimalTimeResponse)
async def get_optimal_times(
    user_id: UserDep = None,
    supabase: SupabaseDep = None,
):
    """
    Get optimal posting times based on X algorithm data.

    Returns best hours for maximum engagement.
    """
    return tweet_scheduler.get_optimal_times()
