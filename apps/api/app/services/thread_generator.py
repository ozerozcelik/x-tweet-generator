"""
Thread Generator service.
Creates multi-tweet threads from a topic or expands a long tweet.
"""

from typing import List, Dict, Optional
from app.services.claude import ClaudeService


class ThreadGenerator:
    """Service for generating tweet threads."""

    def __init__(self):
        self.claude = ClaudeService()

    async def generate_thread(
        self,
        topic: str,
        tweet_count: int = 7,
        style: str = "educational",
        language: str = "tr",
        profile: Optional[Dict] = None,
    ) -> List[str]:
        """
        Generate a tweet thread about a topic.

        Args:
            topic: Thread topic
            tweet_count: Number of tweets to generate
            style: Thread style (educational, storytelling, provocative)
            language: Language code
            profile: User profile for personalization

        Returns:
            List of tweet texts
        """
        prompt = f"""Generate a {tweet_count}-tweet thread about: {topic}

STYLE: {style}
LANGUAGE: {language}

Each tweet should:
- Be under 280 characters (standard limit)
- Flow naturally to the next tweet
- Include appropriate numbering (x/{tweet_count})
- Build engagement throughout
- End with a call-to-action in the final tweet

Format as a numbered list, one tweet per line.
"""

        try:
            tweets = await self.claude.generate_thread(
                topic=topic,
                tweet_count=tweet_count,
                style=style,
                language=language,
                profile=profile,
            )

            # Add numbering if not present
            numbered_tweets = []
            for i, tweet in enumerate(tweets[:tweet_count], 1):
                if not any(f"{i}/{tweet_count}" in tweet for x in range(1, tweet_count + 1)):
                    # Add numbering
                    numbered_tweets.append(f"{i}/{tweet_count} {tweet}")
                else:
                    numbered_tweets.append(tweet)

            return numbered_tweets

        except Exception as e:
            print(f"Thread generation failed: {e}")
            # Fallback
            return [
                f"1/{tweet_count} Let's talk about {topic} 🧵",
                f"2/{tweet_count} Here's what most people don't know...",
                f"3/{tweet_count} The reality is actually quite different.",
                f"4/{tweet_count} Let me explain why this matters...",
                f"5/{tweet_count} Based on my experience...",
                f"6/{tweet_count} Here's what you should do instead:",
                f"7/{tweet_count} Follow for more insights! ✨",
            ][:tweet_count]

    async def expand_to_thread(
        self,
        content: str,
        tweet_count: int = 5,
        profile: Optional[Dict] = None,
    ) -> List[str]:
        """
        Expand a long tweet into a thread.

        Args:
            content: Long tweet content to split
            tweet_count: Target number of tweets
            profile: User profile

        Returns:
            List of tweet texts
        """
        # First, try AI expansion
        try:
            prompt = f"""Convert this long tweet into a {tweet_count}-part thread:

ORIGINAL:
{content}

Break it down so each part:
- Is under 280 characters
- Flows naturally to the next
- Maintains the full message
- Includes numbering (x/{tweet_count})

THREAD:
"""

            tweets = await self.claude.expand_to_thread(
                content=content,
                tweet_count=tweet_count,
                profile=profile,
            )

            if tweets and len(tweets) >= tweet_count - 1:
                # Add numbering if needed
                numbered = []
                for i, tweet in enumerate(tweets[:tweet_count], 1):
                    if f"{i}/{tweet_count}" not in tweet:
                        numbered.append(f"{i}/{tweet_count} {tweet}")
                    else:
                        numbered.append(tweet)
                return numbered

        except Exception:
            pass

        # Fallback: Simple split by sentences
        sentences = content.split('. ')
        tweets = []
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) + 2 <= 280:
                current += sentence + ". "
            else:
                if current:
                    tweets.append(current.strip())
                current = sentence + ". "

        if current:
            tweets.append(current.strip())

        # Add numbering
        numbered = []
        for i, tweet in enumerate(tweets[:tweet_count], 1):
            numbered.append(f"{i}/{len(tweets)} {tweet}")

        # Pad if needed
        while len(numbered) < tweet_count:
            numbered.append(f"{len(numbered) + 1}/{tweet_count} ...")

        return numbered[:tweet_count]

    def get_thread_templates(self) -> List[Dict]:
        """
        Get thread starter templates.

        Returns:
            List of template dictionaries
        """
        return [
            {
                "id": "epic_thread",
                "name": "Epik Thread",
                "template": """🧵 {konu} hakkında kimsenin anlatmadığı gerçekler:

Yıllardır bu alanda çalışıyorum ve gördüklerim sizi şaşırtacak.

Hazırsanız başlıyoruz 👇""",
                "description": "Dikkat çekici thread açılışı",
            },
            {
                "id": "contrarian_thread",
                "name": "Karşıt Görüş",
                "template": """Herkes {yaygın_inanç} diyor.

Ben tam tersini düşünüyorum.

İşte nedeni:

{sebepler}

Unpopular opinion ama arkasındayım.""",
                "description": "Tartışma başlatıcı thread",
            },
            {
                "id": "listicle_thread",
                "name": "Liste Thread",
                "template": """{konu} hakkında bilmeniz gereken {sayı} şey:

Bir sıra ile başlayalım 👇""",
                "description": "Numaralı liste formatı",
            },
            {
                "id": "story_thread",
                "name": "Hikaye Thread",
                "template": """Şu an {konu} hakkında yazdığım en uzun tweet'i okuyun:

{hikaye}

Uzun hikaye kısa: {özet}

Hala okuyorsanız, devam edelim... 🧵""",
                "description": "Hikaye anlatma formatı",
            },
            {
                "id": "mistakes_thread",
                "name": "Hatalar Thread",
                "template": """{konu} konusunda yapılan {sayı} büyük hata:

❌ {hata1}
❌ {hata2}
❌ {hata3}

Bunları yapmayın.""",
                "description": "Hata gösterme formatı",
            },
        ]


# Singleton
_thread_generator: Optional[ThreadGenerator] = None


def get_thread_generator() -> ThreadGenerator:
    """Get or create thread generator singleton."""
    global _thread_generator
    if _thread_generator is None:
        _thread_generator = ThreadGenerator()
    return _thread_generator
