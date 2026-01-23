"""
Free Twitter/X scraper service.
No API key required - uses public frontends and syndication API.
"""

import re
import json
import gzip
import io
import urllib.request
import ssl
from typing import List, Dict, Optional
from dataclasses import dataclass

# SSL context for HTTPS requests
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE


@dataclass
class ScrapedTweet:
    """Scraped tweet data."""
    text: str
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    created_at: Optional[str] = None
    tweet_id: Optional[str] = None


class TwitterScraper:
    """
    Free Twitter/X scraper - No API key required.

    Uses multiple methods:
    1. Twitter Syndication API (unofficial but open)
    2. xcancel.com (public frontend)
    3. Nitter instances (twiiit.com, etc.)
    """

    # Alternative instances (updated Jan 2025)
    ALTERNATIVE_INSTANCES = [
        "xcancel.com",
        "twiiit.com",
        "nitter.privacydev.net",
        "nitter.poast.org",
    ]

    def __init__(self):
        self.working_instance = None
        self.working_method = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def _decompress_response(self, response) -> str:
        """Decompress gzip response."""
        data = response.read()
        if response.info().get('Content-Encoding') == 'gzip':
            try:
                buf = io.BytesIO(data)
                with gzip.GzipFile(fileobj=buf) as f:
                    return f.read().decode('utf-8')
            except:
                pass
        return data.decode('utf-8', errors='ignore')

    def fetch_tweets_syndication(self, username: str, count: int = 50) -> List[ScrapedTweet]:
        """
        Fetch tweets using Twitter Syndication API.

        This is an open endpoint that doesn't require authentication.
        """
        tweets = []
        try:
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"

            headers = {
                **self.headers,
                'Referer': 'https://twitter.com/',
                'Origin': 'https://twitter.com',
            }

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as response:
                html = self._decompress_response(response)

            if not html:
                return []

            # Extract JSON from HTML
            json_pattern = r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>'
            json_match = re.search(json_pattern, html, re.DOTALL)

            if json_match:
                data = json.loads(json_match.group(1))
                timeline = data.get('props', {}).get('pageProps', {}).get('timeline', {})
                entries = timeline.get('entries', [])

                for entry in entries:
                    if entry.get('content', {}).get('entryType') == 'TimelineTweet':
                        tweet_data = entry['content']['itemContent']['tweet_results']['result']
                        legacy = tweet_data.get('legacy', {})

                        text = legacy.get('fullText', '')
                        if not text:
                            continue

                        metrics = legacy.get('core', {}).get('user_result', {}).get('result', {}).get('legacy', {})
                        favorites = metrics.get('favorite_count', 0) or legacy.get('favorite_count', 0)

                        scraped = ScrapedTweet(
                            text=text,
                            likes=int(favorites),
                            retweets=int(legacy.get('retweet_count', 0)),
                            replies=int(legacy.get('reply_count', 0)),
                            views=int(legacy.get('views', {}).get('count', 0)),
                            created_at=legacy.get('created_at'),
                            tweet_id=legacy.get('id_str'),
                        )
                        tweets.append(scraped)

                        if len(tweets) >= count:
                            break

                self.working_method = "syndication"
                return tweets

        except Exception as e:
            print(f"[Syndication] Failed: {e}")

        return []

    def fetch_tweets_xcancel(self, username: str, count: int = 50) -> List[ScrapedTweet]:
        """
        Fetch tweets using xcancel.com (public Twitter frontend).
        """
        tweets = []
        try:
            url = f"https://{self.working_instance}/{username}"

            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as response:
                html = self._decompress_response(response)

            # Parse tweets from HTML
            # xcancel uses a specific structure for tweet content
            tweet_pattern = r'<div[^>]*data-testid="tweet"[^>]*>(.*?)</div>'
            tweets_html = re.findall(tweet_pattern, html, re.DOTALL)

            for tweet_html in tweets_html[:count]:
                # Extract tweet text
                text_match = re.search(r'<div[^>]*data-testid="tweetText"[^>]*>(.*?)</div>', tweet_html, re.DOTALL)
                if text_match:
                    # Clean HTML tags
                    text = re.sub(r'<[^>]+>', '', text_match.group(1))
                    text = text.strip()

                    if text:
                        tweets.append(ScrapedTweet(text=text))

        except Exception as e:
            print(f"[XCancel] Failed: {e}")

        return tweets

    def fetch_tweets_nitter(self, username: str, instance: str, count: int = 50) -> List[ScrapedTweet]:
        """
        Fetch tweets using a Nitter instance.
        """
        tweets = []
        try:
            url = f"https://{instance}/{username}"

            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as response:
                html = self._decompress_response(response)

            # Nitter tweet pattern
            tweet_pattern = r'<div class="timeline-item[^"]*"(.*?)</div>\s*(?=<div class="timeline-item|</main>)'
            tweets_html = re.findall(tweet_pattern, html, re.DOTALL)

            for tweet_html in tweets_html[:count]:
                # Extract tweet text
                text_match = re.search(r'<div class="tweet-content[^>]*>(.*?)</div>', tweet_html, re.DOTALL)
                if text_match:
                    text = re.sub(r'<[^>]+>', '', text_match.group(1))
                    text = text.strip()

                    # Extract stats
                    likes_match = re.search(r'(\d+)\s*Likes', tweet_html)
                    likes = int(likes_match.group(1)) if likes_match else 0

                    if text:
                        tweets.append(ScrapedTweet(text=text, likes=likes))

        except Exception as e:
            print(f"[Nitter:{instance}] Failed: {e}")

        return tweets

    def fetch_tweets(self, username: str, count: int = 50) -> List[Dict]:
        """
        Fetch tweets using multiple methods.

        Tries each method until one succeeds.
        Returns list of tweet dictionaries.
        """
        # Try syndication API first
        tweets = self.fetch_tweets_syndication(username, count)

        if tweets:
            return [
                {
                    "text": t.text,
                    "likes": t.likes,
                    "retweets": t.retweets,
                    "replies": t.replies,
                    "impressions": t.views or 100,
                }
                for t in tweets
            ]

        # Try alternative instances
        for instance in self.ALTERNATIVE_INSTANCES:
            try:
                if "xcancel" in instance or "twiiit" in instance:
                    tweets = self.fetch_tweets_xcancel(username, count)
                else:
                    tweets = self.fetch_tweets_nitter(username, instance, count)

                if tweets:
                    self.working_instance = instance
                    return [
                        {
                            "text": t.text,
                            "likes": t.likes,
                            "retweets": t.retweets or 0,
                            "replies": t.replies or 0,
                            "impressions": t.views or 100,
                        }
                        for t in tweets
                    ]
            except Exception:
                continue

        return []

    def get_status(self) -> Dict:
        """
        Check which scraping methods are working.
        """
        status = {
            "working": False,
            "methods_status": [],
            "working_method": None,
        }

        methods_to_test = [
            ("Syndication API", lambda: self.fetch_tweets_syndication("elonmusk", 5)),
        ]

        for instance in self.ALTERNATIVE_INSTANCES[:2]:  # Test 2 instances
            methods_to_test.append(
                (f"xcancel/{instance}", lambda: self.fetch_tweets_xcancel("elonmusk", 5))
            )

        for method_name, test_func in methods_to_test:
            try:
                result = test_func()
                if result:
                    status["working"] = True
                    status["working_method"] = method_name
                    status["methods_status"].append(f"[OK] {method_name}")
                else:
                    status["methods_status"].append(f"[FAIL] {method_name}")
            except Exception as e:
                status["methods_status"].append(f"[ERROR] {method_name}: {str(e)[:50]}")

        return status


# Singleton instance
_scraper: Optional[TwitterScraper] = None


def get_scraper() -> TwitterScraper:
    """Get or create scraper singleton."""
    global _scraper
    if _scraper is None:
        _scraper = TwitterScraper()
    return _scraper
