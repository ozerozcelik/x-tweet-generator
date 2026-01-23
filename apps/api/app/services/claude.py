"""
Claude AI service for tweet generation.
"""

import os
from typing import Optional, Dict, Any
from anthropic import Anthropic

from app.core.config import settings


class ClaudeService:
    """Service for interacting with Claude AI API."""

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None

    async def generate_tweet(
        self,
        topic: str,
        style: str = "casual",
        tone: str = "engaging",
        length: str = "medium",
        language: str = "tr",
        include_cta: bool = True,
        include_emoji: bool = True,
        custom_instructions: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a tweet using Claude AI.

        Args:
            topic: Tweet topic
            style: Writing style (professional, casual, provocative, etc.)
            tone: Content tone (engaging, controversial, inspirational, etc.)
            length: Tweet length (short, medium, long, epic)
            language: Language code
            include_cta: Whether to include call to action
            include_emoji: Whether to include emojis
            custom_instructions: Additional instructions
            profile: User profile for personalization

        Returns:
            Generated tweet content
        """
        if not self.client:
            return self._generate_fallback_tweet(topic, style, language)

        # Build prompt
        prompt = self._build_generation_prompt(
            topic=topic,
            style=style,
            tone=tone,
            length=length,
            language=language,
            include_cta=include_cta,
            include_emoji=include_emoji,
            custom_instructions=custom_instructions,
            profile=profile,
        )

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract tweet from response
            content = response.content[0].text

            # Clean up response (remove markdown code blocks if present)
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content

            return content.strip()

        except Exception as e:
            print(f"Claude API error: {e}")
            return self._generate_fallback_tweet(topic, style, language)

    def _build_generation_prompt(
        self,
        topic: str,
        style: str,
        tone: str,
        length: str,
        language: str,
        include_cta: bool,
        include_emoji: bool,
        custom_instructions: Optional[str],
        profile: Optional[Dict[str, Any]],
    ) -> str:
        """Build the prompt for tweet generation."""
        prompt = f"""Generate a viral tweet about: {topic}

STYLE: {style}
TONE: {tone}
LENGTH: {length}
LANGUAGE: {language}
INCLUDE CTA: {include_cta}
INCLUDE EMOJI: {include_emoji}
"""

        # Add profile context if available
        if profile:
            prompt += f"\nUSER CONTEXT:\n"
            prompt += f"- Followers: {profile.get('followers', 0)}\n"
            prompt += f"- Verified: {profile.get('verified', False)}\n"
            if profile.get('x_username'):
                prompt += f"- Username: @{profile.get('x_username')}\n"

        # Add custom instructions
        if custom_instructions:
            prompt += f"\nCUSTOM INSTRUCTIONS:\n{custom_instructions}\n"

        prompt += """
Generate ONLY the tweet content, no explanations. The tweet should be:
- Engaging and likely to get interactions
- Optimized for X's algorithm (encourage replies, retweets, likes)
- Natural and authentic sounding
- Under the character limit (280 for standard, 25000 for premium)

TWEET:
"""
        return prompt

    def _generate_fallback_tweet(self, topic: str, style: str, language: str) -> str:
        """Generate a simple fallback tweet without AI."""
        templates = {
            "casual": [
                f"Here's a thought about {topic} that's been on my mind lately...",
                f"Unpopular opinion: {topic} is way more important than people realize.",
                f"Quick thread on {topic} 🧵",
            ],
            "professional": [
                f"Key insight on {topic}:",
                f"Thoughts on the future of {topic}:",
            ],
            "provocative": [
                f"Most people get {topic} completely wrong. Here's why:",
                f"Hot take: {topic} is about to change everything.",
            ],
        }

        import random
        return random.choice(templates.get(style, templates["casual"]))

    async def optimize_tweet(
        self,
        content: str,
        target_score: int,
        original_analysis: Any,
        profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Optimize a tweet to improve its algorithm score."""
        if not self.client:
            return content

        prompt = f"""Optimize this tweet to improve its X algorithm score from {original_analysis.score}/100 to {target_score}/100.

ORIGINAL TWEET:
{content}

WEAKNESSES TO ADDRESS:
{chr(10).join(f"- {w}" for w in original_analysis.weaknesses[:3])}

SUGGESTIONS:
{chr(10).join(f"- {s}" for s in original_analysis.suggestions[:3])}

Rewrite the tweet to:
- Fix the weaknesses
- Implement the suggestions
- Maintain the original message
- Make it more engaging and viral-likely

OPTIMIZED TWEET:
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text.strip()

        except Exception:
            return content

    async def rewrite_tweet(
        self,
        content: str,
        style: str,
        profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Rewrite a tweet in a different style."""
        if not self.client:
            return content

        style_prompts = {
            "viral": "Rewrite this to maximize viral potential and engagement",
            "controversial": "Rewrite this to be thought-provoking and spark discussion",
            "emotional": "Rewrite this to be emotionally resonant and relatable",
            "educational": "Rewrite this to be informative and educational",
        }

        prompt = f"""{style_prompts.get(style, "Rewrite this tweet")}

ORIGINAL TWEET:
{content}

Maintain the core message but transform the style to match the requested tone.

REWRITTEN TWEET:
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text.strip()

        except Exception:
            return content

    async def generate_thread(
        self,
        topic: str,
        tweet_count: int = 7,
        style: str = "educational",
        language: str = "tr",
        profile: Optional[Dict[str, Any]] = None,
    ) -> list[str]:
        """Generate a tweet thread."""
        if not self.client:
            return [f"1/5 Let's talk about {topic}..."] * tweet_count

        prompt = f"""Generate a {tweet_count}-tweet thread about: {topic}

STYLE: {style}
LANGUAGE: {language}

Each tweet should:
- Be under 280 characters
- Flow naturally to the next
- Include appropriate numbering (x/{tweet_count})
- Build engagement throughout the thread

Format as a numbered list of tweets.
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            # Parse into individual tweets
            tweets = []
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    # Remove numbering if present
                    clean = line
                    for i in range(1, tweet_count + 1):
                        clean = clean.replace(f"{i}. ", "").replace(f"{i}/", "")
                    tweets.append(clean.strip())

            return tweets[:tweet_count] or [f"Thread about {topic}"] * tweet_count

        except Exception:
            return [f"Let's talk about {topic}..."] * tweet_count

    async def expand_to_thread(
        self,
        content: str,
        tweet_count: int = 5,
        profile: Optional[Dict[str, Any]] = None,
    ) -> list[str]:
        """Expand a long tweet into a thread."""
        if not self.client:
            return [content[:280] + "..."] * tweet_count

        prompt = f"""Convert this long tweet into a {tweet_count}-part thread:

ORIGINAL:
{content}

Break it down into {tweet_count} connected tweets that:
- Each are under 280 characters
- Flow naturally
- Maintain the full message
- Include numbering (x/{tweet_count})

THREAD:
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            # Parse into individual tweets
            tweets = []
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    tweets.append(line)

            return tweets[:tweet_count] or [content[:280]] * tweet_count

        except Exception:
            return [content[:280]] * tweet_count
