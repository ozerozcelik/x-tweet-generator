"""
Tweet analysis services.
Implements X's algorithm scoring system.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from app.models.tweet import TweetAnalysisResponse, EngagementPrediction


# ============================================================================
# X ALGORITHM WEIGHTS
# ============================================================================

ACTION_WEIGHTS = {
    "favorite": 0.5,
    "reply": 1.0,
    "repost": 1.0,
    "quote": 1.0,
    "follow_author": 4.0,
    "not_interested": -1.0,
}

CONTENT_TYPE_MULTIPLIERS = {
    "text_only": 1.0,
    "with_image": 1.5,
    "with_video": 2.0,
    "with_poll": 1.8,
    "with_link": 0.8,
}

HOURLY_ENGAGEMENT_MULTIPLIERS = {
    0: 0.4, 1: 0.3, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.3,
    6: 0.5, 7: 0.7, 8: 0.9, 9: 1.1, 10: 1.2, 11: 1.3,
    12: 1.4, 13: 1.3, 14: 1.1, 15: 1.0, 16: 1.0, 17: 1.1,
    18: 1.3, 19: 1.4, 20: 1.3, 21: 1.2, 22: 0.9, 23: 0.6,
}


class TweetAnalyzer:
    """Analyzes tweets using X's algorithm scoring system."""

    def __init__(self):
        self.keywords_viral = [
            "secret", "unpopular", "truth about", "nobody talks about",
            "why", "how", "ultimate", "essential", "mistake",
        ]
        self.keywords_engaging = [
            "what do you think", "thoughts", "agree", "disagree",
            "?", "🤔", "💭", "👇",
        ]

    def analyze(self, content: str, profile: Optional[Dict] = None) -> TweetAnalysisResponse:
        """
        Analyze a tweet and return algorithm score.

        Args:
            content: Tweet content to analyze
            profile: Optional user profile for personalization

        Returns:
            TweetAnalysisResponse with score, predictions, and suggestions
        """
        # Calculate base score
        score = 50.0  # Start at neutral

        # Analyze content features
        strengths = []
        weaknesses = []
        suggestions = []

        # Length analysis
        length = len(content)
        if 100 <= length <= 280:
            score += 10
            strengths.append("Optimal length for engagement")
        elif length > 280:
            weaknesses.append("Exceeds standard character limit")
            suggestions.append("Consider shortening or using Premium")
        elif length < 50:
            score -= 5
            weaknesses.append("Very short tweets may lack context")

        # Question analysis
        has_question = "?" in content
        if has_question:
            score += 15
            strengths.append("Contains question - encourages replies")
        else:
            suggestions.append("Add a question to boost replies")

        # Hashtag analysis
        hashtags = re.findall(r"#\w+", content)
        if 1 <= len(hashtags) <= 2:
            score += 5
            strengths.append("Good hashtag usage")
        elif len(hashtags) > 3:
            score -= 10
            weaknesses.append("Too many hashtags reduces reach")

        # Mention analysis
        mentions = re.findall(r"@\w+", content)
        if 1 <= len(mentions) <= 3:
            score += 10
            strengths.append("Strategic mentions increase reach")
        elif len(mentions) > 5:
            score -= 5
            weaknesses.append("Too many mentions may look spammy")

        # Link analysis
        has_link = bool(re.search(r"https?://", content))
        if has_link:
            score -= 10
            weaknesses.append("External links reduce X algorithm reach")
            suggestions.append("Consider using thread or putting link in comments")

        # Emoji analysis
        emojis = len(re.findall(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]", content))
        if 1 <= emojis <= 3:
            score += 5
            strengths.append("Appropriate emoji usage")
        elif emojis > 5:
            score -= 5
            weaknesses.append("Too many emojis")

        # Viral keyword analysis
        has_viral_keyword = any(kw.lower() in content.lower() for kw in self.keywords_viral)
        if has_viral_keyword:
            score += 10
            strengths.append("Contains viral-trigger keywords")

        # Line breaks (readability)
        line_breaks = content.count("\n")
        if 1 <= line_breaks <= 3:
            score += 5
            strengths.append("Good use of spacing for readability")

        # Calculate engagement prediction
        prediction = self._predict_engagement(score, content)

        # Apply profile boost if available
        profile_boost = 1.0
        if profile:
            if profile.get("verified"):
                profile_boost += 0.2
            followers = profile.get("followers", 0)
            if followers >= 10000:
                profile_boost += 0.1
            elif followers >= 100000:
                profile_boost += 0.2

        # Final score with profile boost
        final_score = min(100, score * profile_boost)

        # Generate suggestions based on score
        if final_score < 50:
            suggestions.extend([
                "Add more personality and voice",
                "Include a call-to-action",
                "Make it more relatable",
            ])
        elif final_score < 70:
            suggestions.extend([
                "Consider adding a controversial take",
                "Add more specific examples",
            ])

        return TweetAnalysisResponse(
            score=min(100, max(0, final_score)),
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            engagement_prediction=prediction,
            profile_boost=profile_boost,
        )

    def _predict_engagement(self, score: float, content: str) -> EngagementPrediction:
        """Predict engagement rates based on score and content."""
        base_rate = score / 100  # 0-1

        # Adjust based on content
        if "?" in content:
            base_rate *= 1.2  # Questions get more replies
        if re.search(r"https?://", content):
            base_rate *= 0.7  # Links reduce engagement

        return EngagementPrediction(
            favorite=min(0.15, base_rate * 0.15),
            reply=min(0.08, base_rate * 0.08 if "?" in content else base_rate * 0.03),
            repost=min(0.05, base_rate * 0.05),
            quote=min(0.03, base_rate * 0.03),
            follow_author=min(0.02, base_rate * 0.02),
        )


class TweetStyleAnalyzer:
    """Analyzes user's tweet writing style."""

    def __init__(self):
        pass

    def analyze_tweets(self, tweets: List[Dict]) -> Dict:
        """Analyze a collection of tweets to determine writing style."""
        if not tweets:
            return self._empty_analysis()

        total_length = sum(len(t.get("text", "")) for t in tweets)
        avg_length = total_length / len(tweets)

        # Count features
        total_line_breaks = sum(t.get("text", "").count("\n") for t in tweets)
        avg_line_breaks = total_line_breaks / len(tweets)

        # Emoji frequency
        emoji_pattern = re.compile(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]")
        total_emojis = sum(len(emoji_pattern.findall(t.get("text", ""))) for t in tweets)
        emoji_frequency = total_emojis / len(tweets)

        # Question frequency
        total_questions = sum(1 for t in tweets if "?" in t.get("text", ""))
        question_frequency = total_questions / len(tweets)

        # Hashtag frequency
        total_hashtags = sum(len(re.findall(r"#\w+", t.get("text", ""))) for t in tweets)
        hashtag_frequency = total_hashtags / len(tweets)

        # Mention frequency
        total_mentions = sum(len(re.findall(r"@\w+", t.get("text", ""))) for t in tweets)
        mention_frequency = total_mentions / len(tweets)

        # Common emojis
        all_emojis = []
        for t in tweets:
            all_emojis.extend(emoji_pattern.findall(t.get("text", "")))
        common_emojis = list(set(all_emojis))[:5]

        # Common words
        all_words = []
        for t in tweets:
            text = t.get("text", "")
            words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
            all_words.extend(words)

        from collections import Counter
        word_counts = Counter(all_words)
        common_words = [w for w, c in word_counts.most_common(10)]

        # Detect tone
        tone = self._detect_tweet_tone(tweets)

        # Calculate engagement rate
        total_likes = sum(t.get("likes", 0) for t in tweets)
        total_impressions = sum(t.get("impressions", 100) for t in tweets)
        avg_engagement_rate = total_likes / total_impressions if total_impressions > 0 else None

        # Generate style prompt
        style_prompt = self._generate_style_prompt(
            avg_length=avg_length,
            emoji_frequency=emoji_frequency,
            question_frequency=question_frequency,
            tone=tone,
            common_emojis=common_emojis,
        )

        return {
            "avg_length": avg_length,
            "avg_line_breaks": avg_line_breaks,
            "emoji_frequency": emoji_frequency,
            "question_frequency": question_frequency,
            "hashtag_frequency": hashtag_frequency,
            "mention_frequency": mention_frequency,
            "tone": tone,
            "common_emojis": common_emojis,
            "common_words": common_words,
            "avg_engagement_rate": avg_engagement_rate,
            "style_prompt": style_prompt,
        }

    def _empty_analysis(self) -> Dict:
        """Return empty analysis result."""
        return {
            "avg_length": 0,
            "avg_line_breaks": 0,
            "emoji_frequency": 0,
            "question_frequency": 0,
            "hashtag_frequency": 0,
            "mention_frequency": 0,
            "tone": "neutral",
            "common_emojis": [],
            "common_words": [],
            "avg_engagement_rate": None,
            "style_prompt": "Write in a casual, engaging tone",
        }

    def _detect_tone(self, tweets: List[Dict]) -> str:
        """Detect the overall tone of tweets."""
        professional_count = 0
        casual_count = 0
        provocative_count = 0

        for t in tweets:
            text = t.get("text", "").lower()

            professional_keywords = ["according to", "research", "study", "analysis", "data"]
            casual_keywords = ["lol", "haha", "omg", "literally", "tbh", "imo"]
            provocative_keywords = ["unpopular", "controversial", "hot take", "truth about"]

            if any(kw in text for kw in professional_keywords):
                professional_count += 1
            if any(kw in text for kw in casual_keywords):
                casual_count += 1
            if any(kw in text for kw in provocative_keywords):
                provocative_count += 1

        counts = {
            "professional": professional_count,
            "casual": casual_count,
            "provocative": provocative_count,
        }

        return max(counts, key=counts.get) or "neutral"

    def _generate_style_prompt(
        self,
        avg_length: float,
        emoji_frequency: float,
        question_frequency: float,
        tone: str,
        common_emojis: List[str],
    ) -> str:
        """Generate an AI prompt matching the user's style."""
        prompt_parts = []

        # Length guidance
        if avg_length < 100:
            prompt_parts.append("Keep tweets concise and punchy")
        elif avg_length > 200:
            prompt_parts.append("Write longer, more detailed tweets")

        # Emoji guidance
        if emoji_frequency > 1:
            emoji_str = " ".join(common_emojis[:3])
            prompt_parts.append(f"Use these emojis frequently: {emoji_str}")
        elif emoji_frequency > 0.5:
            prompt_parts.append("Use emojis occasionally")
        else:
            prompt_parts.append("Rarely use emojis")

        # Question guidance
        if question_frequency > 0.5:
            prompt_parts.append("Frequently ask questions to engage readers")

        # Tone
        prompt_parts.append(f"Write in a {tone} tone")

        return ". ".join(prompt_parts) + "."


class TweetCredAnalyzer:
    """Analyzes TweetCred score (X's authority system)."""

    TWEETCRED_DEFAULT = -128
    TWEETCRED_VERIFIED_BOOST = 100
    TWEETCRED_MIN_POSITIVE = 17

    def calculate_tweetcred(
        self,
        followers: int = 0,
        verified: bool = False,
        following: int = 0,
        account_age_days: int = 365,
        avg_engagement_rate: float = 0.01,
    ) -> Dict:
        """Calculate TweetCred score."""
        score = self.TWEETCRED_DEFAULT

        # Verified boost
        verified_boost = self.TWEETCRED_VERIFIED_BOOST if verified else 0
        score += verified_boost

        # Bio score (placeholder - would need actual bio data)
        bio_score = 10  # Assume decent bio
        score += bio_score

        # Follower ratio score
        if following > 0:
            ratio = followers / following
            if ratio >= 10:
                ratio_score = 30
            elif ratio >= 5:
                ratio_score = 20
            elif ratio >= 2:
                ratio_score = 15
            elif ratio >= 1:
                ratio_score = 10
            else:
                ratio_score = -10
        else:
            ratio_score = 10 if followers > 100 else 0
        score += ratio_score

        # Engagement history score
        if avg_engagement_rate >= 0.05:
            engagement_score = 40
        elif avg_engagement_rate >= 0.03:
            engagement_score = 30
        elif avg_engagement_rate >= 0.02:
            engagement_score = 20
        elif avg_engagement_rate >= 0.01:
            engagement_score = 10
        else:
            engagement_score = -20
        score += engagement_score

        # Account age bonus
        if account_age_days >= 365 * 3:
            age_bonus = 15
        elif account_age_days >= 365:
            age_bonus = 10
        elif account_age_days >= 180:
            age_bonus = 5
        else:
            age_bonus = 0
        score += age_bonus

        # Niche focus (placeholder)
        niche_score = 15
        score += niche_score

        # Calculate derived values
        is_positive = score >= self.TWEETCRED_MIN_POSITIVE
        has_cold_start = score <= -50

        if has_cold_start:
            distribution_rate = 0.10
        elif not is_positive:
            distribution_rate = 0.30
        elif score >= 50:
            distribution_rate = 1.0
        else:
            distribution_rate = 0.5 + (score / 200)

        return {
            "total_score": score,
            "base_score": self.TWEETCRED_DEFAULT,
            "verified_boost": verified_boost,
            "bio_score": bio_score,
            "ratio_score": ratio_score,
            "language_score": 5,  # Placeholder
            "engagement_history_score": engagement_score,
            "niche_focus_score": niche_score,
            "is_positive": is_positive,
            "has_cold_start_suppression": has_cold_start,
            "distribution_rate": round(distribution_rate, 2),
        }


class MonetizationAnalyzer:
    """Analyzes monetization potential."""

    RPM_BY_COUNTRY = {
        "US": 4.0,
        "EU": 2.0,
        "TR": 0.25,
        "OTHER": 0.5,
    }

    NICHE_PROFITABILITY = {
        "finans": "high",
        "kripto": "high",
        "teknoloji": "medium",
        "eglence": "medium",
        "spor": "medium",
        "genel": "low",
    }

    def get_monetization_analysis(
        self,
        followers: int,
        country: str = "TR",
        niche: str = "genel",
        avg_engagement_rate: float = 0.01,
    ) -> Dict:
        """Get monetization analysis."""
        rpm = self.RPM_BY_COUNTRY.get(country, self.RPM_BY_COUNTRY["OTHER"])

        # Adjust by niche
        niche_quality = self.NICHE_PROFITABILITY.get(niche, "low")
        if niche_quality == "high":
            rpm *= 2
        elif niche_quality == "medium":
            rpm *= 1.2

        # Calculate monthly potential (assuming 3 tweets/day, 10% reach)
        daily_impressions = followers * 0.1 * 3 if followers > 0 else 100
        monthly_impressions = daily_impressions * 30
        monthly_potential = (monthly_impressions / 1000) * rpm

        # Generate tips
        tips = []
        warnings = []

        if country == "TR":
            warnings.append("Turkey has lower RPM - consider targeting US/UK audience")
            tips.append("Write in English to reach higher-paying markets")

        if niche == "genel":
            tips.append("Focus on a specific niche to increase RPM")
            tips.append("Consider: finance, crypto, or tech content")

        if avg_engagement_rate < 0.02:
            tips.append("Improve engagement rate to increase monetization eligibility")

        # Recommended niches
        recommended_niches = []
        if country != "US":
            recommended_niches.extend(["crypto", "trading", "saas", "ai"])

        return {
            "estimated_rpm": round(rpm, 2),
            "niche_profitability": niche_quality,
            "target_market": country,
            "recommended_niches": recommended_niches,
            "tips": tips,
            "warnings": warnings,
            "monthly_potential": round(monthly_potential, 2),
        }


class TweetScheduler:
    """Manages tweet scheduling and optimal time recommendations."""

    def get_optimal_times(self) -> Dict:
        """Get optimal posting times."""
        from datetime import datetime
        import pytz

        now = datetime.now(pytz.timezone("Europe/Istanbul"))
        current_hour = now.hour
        current_day = now.weekday()

        # Get current hour multiplier
        current_score = HOURLY_ENGAGEMENT_MULTIPLIERS.get(current_hour, 1.0)

        # Build best hours list
        best_hours = []
        for hour, multiplier in sorted(HOURLY_ENGAGEMENT_MULTIPLIERS.items(), key=lambda x: x[1], reverse=True):
            if multiplier >= 1.2:
                label = "Peak"
            elif multiplier >= 1.0:
                label = "Good"
            else:
                continue

            best_hours.append({
                "hour": hour,
                "multiplier": multiplier,
                "time": f"{hour:02d}:00",
                "label": label,
            })

        # Generate recommendation
        if current_score >= 1.3:
            recommendation = "Great time to post! Engagement is at peak levels."
            quality = "Excellent"
        elif current_score >= 1.0:
            recommendation = "Good time to post. Engagement is above average."
            quality = "Good"
        else:
            recommendation = "Consider waiting. Engagement is lower right now."
            quality = "Low"

        return {
            "current": {
                "hour": current_hour,
                "day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][current_day],
                "score": int(current_score * 100),
                "quality": quality,
            },
            "best_hours": best_hours[:10],
            "recommendation": recommendation,
        }
