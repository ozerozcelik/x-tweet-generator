"""
A/B Testing API routes.
Campaign management and result analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
import uuid

from app.core.deps import SupabaseDep, UserDep
from app.models.ab_test import (
    AbCampaignCreate,
    AbCampaignResponse,
    AbResultsResponse,
    SetWinnerRequest,
)

router = APIRouter()


@router.post("/campaigns", response_model=AbCampaignResponse)
async def create_ab_campaign(
    request: AbCampaignCreate,
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """
    Create an A/B test campaign.

    Each campaign can have 2-5 tweet variants to test.
    """
    try:
        # Create campaign
        campaign_id = str(uuid.uuid4())
        campaign = {
            "id": campaign_id,
            "user_id": user_id,
            "name": request.name,
            "status": "running",
            "started_at": datetime.now().isoformat(),
        }

        supabase.table("ab_campaigns").insert(campaign).execute()

        # Create variants
        for i, content in enumerate(request.variants):
            # First create the tweet
            tweet_result = supabase.table("tweets").insert({
                "user_id": user_id,
                "content": content,
                "status": "ab_test",
            }).select("*").single().execute()

            # Link to campaign
            supabase.table("ab_variants").insert({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "tweet_id": tweet_result.data["id"],
                "is_winner": False,
            }).execute()

        return AbCampaignResponse(**campaign, ended_at=None)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )


@router.get("/campaigns")
async def get_ab_campaigns(
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """Get all A/B test campaigns for the user."""
    try:
        result = supabase.table("ab_campaigns") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .execute()

        return result.data or []

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch campaigns: {str(e)}"
        )


@router.get("/campaigns/{campaign_id}/results", response_model=AbResultsResponse)
async def get_ab_results(
    campaign_id: str,
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """
    Get A/B test results for a campaign.

    Includes performance metrics for each variant.
    """
    try:
        # Get campaign
        campaign_result = supabase.table("ab_campaigns") \
            .select("*") \
            .eq("id", campaign_id) \
            .eq("user_id", user_id) \
            .single() \
            .execute()

        if not campaign_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Get variants with tweet content
        variants_result = supabase.table("ab_variants") \
            .select("*, tweets(content)") \
            .eq("campaign_id", campaign_id) \
            .execute()

        variants = []
        winner = None

        for v in variants_result.data or []:
            variant_data = {
                "id": v["id"],
                "campaign_id": v["campaign_id"],
                "content": v.get("tweets", {}).get("content", ""),
                "is_winner": v["is_winner"],
                "impressions": v.get("impressions", 0),
                "likes": v.get("likes", 0),
                "retweets": v.get("retweets", 0),
                "replies": v.get("replies", 0),
                "created_at": v["created_at"],
            }
            variants.append(variant_data)

            if v["is_winner"]:
                winner = variant_data

        # Calculate statistical significance (simplified)
        # In production, use proper statistical tests
        stat_significance = None
        if len(variants) >= 2 and variants[0]["impressions"] > 100:
            # Simple calculation - should use proper statistical test
            stat_significance = 0.95  # Placeholder

        return AbResultsResponse(
            campaign_id=campaign_id,
            campaign_name=campaign_result.data["name"],
            status=campaign_result.data["status"],
            variants=variants,
            winner=winner,
            statistical_significance=stat_significance,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch results: {str(e)}"
        )


@router.post("/campaigns/{campaign_id}/winner")
async def set_ab_winner(
    campaign_id: str,
    request: SetWinnerRequest,
    user_id: UserDep,
    supabase: SupabaseDep,
):
    """
    Set the winning variant for an A/B test.

    This will mark the selected variant as the winner.
    """
    try:
        # Verify campaign ownership
        campaign_result = supabase.table("ab_campaigns") \
            .select("*") \
            .eq("id", campaign_id) \
            .eq("user_id", user_id) \
            .single() \
            .execute()

        if not campaign_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Clear previous winner
        supabase.table("ab_variants") \
            .update({"is_winner": False}) \
            .eq("campaign_id", campaign_id) \
            .execute()

        # Set new winner
        supabase.table("ab_variants") \
            .update({"is_winner": True}) \
            .eq("id", request.variant_id) \
            .eq("campaign_id", campaign_id) \
            .execute()

        # Update campaign status
        supabase.table("ab_campaigns") \
            .update({
                "status": "completed",
                "ended_at": datetime.now().isoformat()
            }) \
            .eq("id", campaign_id) \
            .execute()

        return {"message": "Winner set successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set winner: {str(e)}"
        )
