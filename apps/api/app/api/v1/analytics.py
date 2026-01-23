"""
Analytics API routes.
Performance metrics and insights.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timedelta

from app.core.deps import SupabaseDep, UserDep

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview(
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """
    Get analytics overview for the user.

    Includes tweet counts, average performance, and trends.
    """
    try:
        # Get all tweets
        tweets_result = supabase.table("tweets") \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()

        tweets = tweets_result.data or []

        # Calculate metrics
        total_tweets = len(tweets)
        draft_count = sum(1 for t in tweets if t.get("status") == "draft")
        scheduled_count = sum(1 for t in tweets if t.get("status") == "scheduled")
        posted_count = sum(1 for t in tweets if t.get("status") == "posted")

        # Average algorithm score
        scores = [
            t.get("analysis", {}).get("score", 0)
            for t in tweets
            if t.get("analysis") and isinstance(t.get("analysis"), dict)
        ]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Recent activity (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recent_tweets = [
            t for t in tweets
            if t.get("created_at") and t.get("created_at") > week_ago
        ]

        return {
            "total_tweets": total_tweets,
            "draft_count": draft_count,
            "scheduled_count": scheduled_count,
            "posted_count": posted_count,
            "avg_score": round(avg_score, 1),
            "recent_activity": len(recent_tweets),
            "high_performers": sum(1 for s in scores if s >= 70),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}"
        )


@router.get("/performance")
async def get_performance_data(
    user_id: UserDep,
    supabase: SupabaseDep,
    days: int = 30,
):
    """
    Get performance data over time.

    Returns daily statistics for the specified period.
    """
    try:
        # Get tweets from the specified period
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        tweets_result = supabase.table("tweets") \
            .select("*") \
            .eq("user_id", user_id) \
            .gte("created_at", start_date) \
            .order("created_at", desc=False) \
            .execute()

        tweets = tweets_result.data or []

        # Group by date
        daily_data = {}
        for tweet in tweets:
            created_at = tweet.get("created_at", "")
            if created_at:
                date = created_at.split("T")[0]
                if date not in daily_data:
                    daily_data[date] = {
                        "date": date,
                        "count": 0,
                        "total_score": 0,
                    }
                daily_data[date]["count"] += 1
                score = tweet.get("analysis", {}).get("score", 0) or 0
                daily_data[date]["total_score"] += score

        # Calculate averages and format response
        performance_data = []
        for date, data in sorted(daily_data.items()):
            performance_data.append({
                "date": date,
                "count": data["count"],
                "avg_score": round(data["total_score"] / data["count"], 1) if data["count"] > 0 else 0,
            })

        return performance_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch performance data: {str(e)}"
        )
