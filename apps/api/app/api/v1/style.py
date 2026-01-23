"""
Style Analysis API routes.
User style learning and personalized tweet generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import SupabaseDep, UserDep
from app.models.profile import StyleAnalysisRequest, StyleAnalysisResponse
from app.services.analyzer import TweetStyleAnalyzer

router = APIRouter()


@router.post("/analyze-style", response_model=StyleAnalysisResponse)
async def analyze_style(
    request: StyleAnalysisRequest,
    user_id: UserDep,
    supabase: SupabaseDep = None,
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
            "analysis_data": analysis,
        }).execute()
    except Exception:
        pass  # Don't fail if save fails

    return analysis


@router.get("/my-style")
async def get_my_style(
    user_id: UserDep,
    supabase: SupabaseDep = None,
):
    """
    Get user's saved style analysis.

    Returns the most recent style analysis for the user.
    """
    try:
        result = supabase.table("style_analyses") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(1) \
            .single() \
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No style analysis found. Please analyze your tweets first."
            )

        return result.data.get("analysis_data", {})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch style analysis: {str(e)}"
        )


@router.post("/generate-in-style")
async def generate_in_style(
    topic: str,
    user_id: UserDep,
    supabase: SupabaseDep = None,
):
    """
    Generate a tweet in user's writing style.

    Uses previously saved style analysis to personalize the output.
    """
    # Get user's style analysis
    try:
        result = supabase.table("style_analyses") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(1) \
            .single() \
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No style analysis found. Please analyze your tweets first."
            )

        style_data = result.data.get("analysis_data", {})

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch style analysis"
        )

    # Use style prompt to generate tweet
    from app.services.claude import ClaudeService

    claude = ClaudeService()
    style_prompt = style_data.get("style_prompt", "Write in a casual, engaging tone")

    prompt = f"""Generate a tweet about: {topic}

STYLE INSTRUCTIONS:
{style_prompt}

Make it viral-optimized while keeping the user's authentic voice.

TWEET:
"""

    try:
        response = claude.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text.strip()

        return {
            "content": content,
            "style_used": {
                "tone": style_data.get("tone"),
                "avg_length": style_data.get("avg_length"),
                "emoji_frequency": style_data.get("emoji_frequency"),
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tweet: {str(e)}"
        )
