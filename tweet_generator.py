"""
X Algorithm-Based Tweet Generator
Based on: https://github.com/xai-org/x-algorithm

Bu tool, X'in For You algoritmasının puanlama sistemine göre
tweet'lerinizi optimize etmenize yardımcı olur.

AI-powered yaratıcı tweet üretimi için Claude API kullanır.
"""

import re
import json
import random
import os
import urllib.request
import urllib.error
import ssl
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

# SSL context for HTTPS requests (ignore certificate errors)
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# Claude API için
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# X API için
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

# Requests kütüphanesi (daha güvenilir HTTP client)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ntscraper kütüphanesi (Nitter tabanlı scraper)
try:
    from ntscraper import Nitter
    NTSCRAPER_AVAILABLE = True
except ImportError:
    NTSCRAPER_AVAILABLE = False


class ActionType(Enum):
    """X algoritmasının tahmin ettiği 15 eylem türü"""
    FAVORITE = "favorite"
    REPLY = "reply"
    REPOST = "repost"
    QUOTE = "quote"
    CLICK = "click"
    PROFILE_CLICK = "profile_click"
    VIDEO_VIEW = "video_view"
    PHOTO_EXPAND = "photo_expand"
    SHARE = "share"
    DWELL = "dwell"
    FOLLOW_AUTHOR = "follow_author"
    NOT_INTERESTED = "not_interested"
    BLOCK_AUTHOR = "block_author"
    MUTE_AUTHOR = "mute_author"
    REPORT = "report"


# ============================================================================
# X ALGORİTMASI AĞIRLIKLARI (Rust codebase analizi - Ocak 2025)
# Kaynak: Phoenix WeightedScorer, AuthorDiversityScorer, OONScorer
# ============================================================================

# Pozitif Sinyaller - Engagement aksiyonları
ACTION_WEIGHTS = {
    # Core engagement (yüksek değerli)
    ActionType.FAVORITE: 0.5,           # ServerTweetFav
    ActionType.REPLY: 1.0,              # ServerTweetReply - Yüksek değer (conversation starter)
    ActionType.REPOST: 1.0,             # ServerTweetRetweet
    ActionType.QUOTE: 1.0,              # ServerTweetQuote - En değerli (orijinal içerik + amplification)

    # Click aksiyonları (orta değer)
    ActionType.CLICK: 0.5,              # ClientTweetClick
    ActionType.PROFILE_CLICK: 1.0,      # ClientTweetClickProfile - Yüksek (discovery)
    ActionType.PHOTO_EXPAND: 0.5,       # ClientTweetPhotoExpand

    # Video aksiyonları
    ActionType.VIDEO_VIEW: 0.3,         # ClientTweetVideoQualityView (VQV) - sadece uzun videolar için

    # Share aksiyonları (en değerli - off-platform amplification)
    ActionType.SHARE: 1.0,              # ClientTweetShare
    ActionType.DWELL: 0.25,             # ClientTweetRecapDwelled (kısa okuma)

    # Follow - en yüksek değer
    ActionType.FOLLOW_AUTHOR: 4.0,      # ClientTweetFollowAuthor - Critical signal

    # Negatif sinyaller (skoru düşürür)
    ActionType.NOT_INTERESTED: -1.0,    # ClientTweetNotInterestedIn
    ActionType.BLOCK_AUTHOR: -1.0,      # ClientTweetBlockAuthor
    ActionType.MUTE_AUTHOR: -1.0,       # ClientTweetMuteAuthor
    ActionType.REPORT: -1.0,            # ClientTweetReport
}

# Genişletilmiş ağırlıklar (ek sinyaller)
EXTENDED_WEIGHTS = {
    "share_via_dm": 1.5,                # DM ile paylaşım - çok değerli (private recommendation)
    "share_via_copy_link": 1.0,         # Link kopyalama - off-platform share
    "quoted_click": 0.5,                # Quote tweet'e tıklama
    "dwell_time_continuous": 0.1,       # Saniye başına dwell time bonus
    "bookmark": 1.0,                    # Bookmark (tahmini)
}

# Author Diversity Scorer parametreleri
AUTHOR_DIVERSITY_DECAY = 0.5           # Her tekrar eden yazar için %50 decay
AUTHOR_DIVERSITY_FLOOR = 0.1           # Minimum multiplier (asla 0'a düşmez)

# Out-of-Network (OON) adjustment
OON_WEIGHT_FACTOR = 0.8                # Takip etmediğin kişilerin tweetleri %20 penalty

# Negative score offset (negatif skorları normalize etmek için)
NEGATIVE_SCORES_OFFSET = 1.0

# X Premium karakter limiti
MAX_CHARS_STANDARD = 280
MAX_CHARS_PREMIUM = 25000

# TweetCred Skoru Sabitleri (Jack'in geliştirdiği otorite skalası)
TWEETCRED_DEFAULT = -128  # Her hesap buradan başlar
TWEETCRED_VERIFIED_BOOST = 100  # Mavi tik +100 puan
TWEETCRED_MIN_POSITIVE = 17  # Bu skora ulaşmadan erişim neredeyse sıfır
TWEETCRED_COLD_START_THRESHOLD = -50  # Bu skorun altında cold start suppression

# Engagement Debt Sabitleri
ENGAGEMENT_DEBT_THRESHOLD = 0.005  # %0.5 like/impression oranı
COLD_START_DISTRIBUTION = 0.10  # %10 dağıtım (cold start suppression aktifken)

# Dwell Time Sabitleri
DWELL_TIME_MIN_SECONDS = 3  # 3 saniyeden az = negatif sinyal
DWELL_TIME_QUALITY_PENALTY = 0.15  # %15-20 quality multiplier düşüşü

# Türkiye Reklam Nişleri (yerli markalar)
TR_PROFITABLE_NICHES = [
    "finans", "banka", "borsa", "kripto", "yatırım",
    "bahis", "iddia", "casino",
    "e-ticaret", "pazaryeri", "alışveriş",
    "teknoloji", "yazılım", "startup"
]

# Global Karlı Nişler (US/EU reklamverenler)
GLOBAL_PROFITABLE_NICHES = [
    "crypto", "trading", "forex", "stocks", "investment",
    "saas", "tech", "ai", "fintech",
    "marketing", "business", "entrepreneurship"
]

# ============================================================================
# TWEET ZAMANLAMA OPTİMİZASYONU (Twitter Analytics verilerine dayalı)
# ============================================================================

# Saat bazlı engagement multiplier (UTC+3 Türkiye saati)
# 1.0 = ortalama, >1.0 = yüksek engagement, <1.0 = düşük engagement
HOURLY_ENGAGEMENT_MULTIPLIERS = {
    0: 0.4,   # 00:00 - Gece yarısı (çok düşük)
    1: 0.3,   # 01:00
    2: 0.2,   # 02:00
    3: 0.2,   # 03:00
    4: 0.2,   # 04:00
    5: 0.3,   # 05:00
    6: 0.5,   # 06:00 - Sabah uyanış
    7: 0.7,   # 07:00
    8: 0.9,   # 08:00 - İş başlangıcı
    9: 1.1,   # 09:00 - Prime time başlangıcı
    10: 1.2,  # 10:00
    11: 1.3,  # 11:00 - Öğle öncesi peak
    12: 1.4,  # 12:00 - ÖĞLE PEAK
    13: 1.3,  # 13:00
    14: 1.1,  # 14:00
    15: 1.0,  # 15:00
    16: 1.0,  # 16:00
    17: 1.1,  # 17:00 - İş çıkışı
    18: 1.3,  # 18:00 - AKŞAM PEAK
    19: 1.4,  # 19:00 - EN YÜKSEK
    20: 1.3,  # 20:00
    21: 1.2,  # 21:00
    22: 0.9,  # 22:00
    23: 0.6,  # 23:00
}

# Gün bazlı engagement multiplier
# Pazartesi=0, Pazar=6
DAILY_ENGAGEMENT_MULTIPLIERS = {
    0: 0.9,   # Pazartesi - Hafta başı yoğunluğu
    1: 1.0,   # Salı - Normal
    2: 1.1,   # Çarşamba - Peak gün
    3: 1.1,   # Perşembe - Peak gün
    4: 1.0,   # Cuma - Hafta sonu öncesi
    5: 0.8,   # Cumartesi - Düşük
    6: 0.7,   # Pazar - En düşük
}

# Tweet içerik tipi multiplier'ları
CONTENT_TYPE_MULTIPLIERS = {
    "text_only": 1.0,           # Sadece metin
    "with_image": 1.5,          # Görsel içerik +50%
    "with_video": 2.0,          # Video içerik +100%
    "with_poll": 1.8,           # Anket +80%
    "with_link": 0.8,           # Harici link -20% (Twitter linki sevmez)
    "thread": 1.3,              # Thread +30%
    "reply": 0.6,               # Reply düşük reach
    "quote": 1.2,               # Quote tweet +20%
}

# Optimal posting saatleri (Türkiye için)
OPTIMAL_POSTING_HOURS_TR = [
    {"hour": 12, "day_range": "weekday", "description": "Öğle molası", "score": 95},
    {"hour": 19, "day_range": "weekday", "description": "Akşam prime time", "score": 100},
    {"hour": 9, "day_range": "weekday", "description": "İş başlangıcı", "score": 85},
    {"hour": 18, "day_range": "weekday", "description": "İş çıkışı", "score": 90},
    {"hour": 21, "day_range": "all", "description": "Gece scrolling", "score": 80},
    {"hour": 11, "day_range": "weekend", "description": "Hafta sonu brunch", "score": 75},
]

# Viral potansiyel faktörleri
VIRAL_FACTORS = {
    "controversial_topic": 2.5,    # Tartışmalı konu
    "breaking_news": 3.0,          # Son dakika haberi
    "trending_hashtag": 2.0,       # Trend hashtag kullanımı
    "celebrity_mention": 2.0,      # Ünlü mention
    "humor": 1.8,                  # Mizah içerik
    "relatable": 1.5,              # İlişkilendirilebilir içerik
    "educational": 1.3,            # Eğitici içerik
    "personal_story": 1.4,         # Kişisel hikaye
}


@dataclass
class TweetAnalysis:
    """Tweet analiz sonucu"""
    score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    engagement_prediction: Dict[str, float]
    profile_boost: float = 1.0  # Profil bazlı çarpan


@dataclass
class XProfile:
    """X Profil bilgileri"""
    username: str
    name: str
    followers_count: int
    following_count: int
    tweet_count: int
    created_at: str
    verified: bool
    description: str
    profile_image_url: str = ""

    @property
    def account_age_days(self) -> int:
        """Hesap yaşını gün olarak hesapla"""
        from datetime import datetime
        try:
            created = datetime.strptime(self.created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            return (datetime.now() - created).days
        except:
            return 0

    @property
    def follower_ratio(self) -> float:
        """Takipçi/Takip oranı"""
        if self.following_count == 0:
            return self.followers_count
        return self.followers_count / self.following_count

    @property
    def engagement_tier(self) -> str:
        """Hesap seviyesi"""
        if self.followers_count >= 1000000:
            return "mega"  # 1M+
        elif self.followers_count >= 100000:
            return "macro"  # 100K+
        elif self.followers_count >= 10000:
            return "mid"  # 10K+
        elif self.followers_count >= 1000:
            return "micro"  # 1K+
        elif self.followers_count >= 100:
            return "nano"  # 100+
        else:
            return "starter"  # <100


@dataclass
class TweetCredScore:
    """
    TweetCred Skoru - Jack'in geliştirdiği hesap otorite skalası

    Her hesap -128'den başlar.
    Minimum +17'ye ulaşmadan erişim gücü neredeyse sıfır.
    Verified hesaplar +100 boost alır (-28'den başlar).
    """
    base_score: int = TWEETCRED_DEFAULT
    verified_boost: int = 0
    bio_score: int = 0
    ratio_score: int = 0
    language_score: int = 0
    engagement_history_score: int = 0
    niche_focus_score: int = 0

    @property
    def total_score(self) -> int:
        """Toplam TweetCred skoru"""
        return (
            self.base_score +
            self.verified_boost +
            self.bio_score +
            self.ratio_score +
            self.language_score +
            self.engagement_history_score +
            self.niche_focus_score
        )

    @property
    def is_positive(self) -> bool:
        """Skor pozitif mi?"""
        return self.total_score >= TWEETCRED_MIN_POSITIVE

    @property
    def has_cold_start_suppression(self) -> bool:
        """Cold start suppression aktif mi?"""
        return self.total_score <= TWEETCRED_COLD_START_THRESHOLD

    @property
    def distribution_rate(self) -> float:
        """Post dağıtım oranı"""
        if self.has_cold_start_suppression:
            return COLD_START_DISTRIBUTION  # %10
        elif not self.is_positive:
            return 0.3  # %30
        elif self.total_score >= 50:
            return 1.0  # %100
        else:
            return 0.5 + (self.total_score / 100)  # %50-100 arası


@dataclass
class EngagementDebt:
    """
    Engagement Debt - Algoritmik Borç Sistemi

    İlk 100 post'ta %0.5'ten düşük like/impression oranı varsa,
    skor kalıcı olarak -50'ye kadar düşebilir ve
    "cold start suppression" modunu tetikler.
    """
    total_posts: int = 0
    total_likes: int = 0
    total_impressions: int = 0
    debt_level: float = 0.0  # 0-1 arası, 1 = maksimum borç

    @property
    def engagement_rate(self) -> float:
        """Like/Impression oranı"""
        if self.total_impressions == 0:
            return 0.0
        return self.total_likes / self.total_impressions

    @property
    def has_debt(self) -> bool:
        """Engagement borcu var mı?"""
        return (
            self.total_posts >= 10 and
            self.engagement_rate < ENGAGEMENT_DEBT_THRESHOLD
        )

    @property
    def severity(self) -> str:
        """Borç şiddeti"""
        if not self.has_debt:
            return "none"
        rate = self.engagement_rate
        if rate < 0.001:
            return "critical"  # %0.1'in altı
        elif rate < 0.003:
            return "severe"  # %0.3'ün altı
        else:
            return "moderate"  # %0.5'in altı


@dataclass
class MonetizationAnalysis:
    """X'den para kazanma analizi"""
    estimated_rpm: float  # Revenue per mille (1000 görüntülenme başına gelir)
    niche_profitability: str  # low, medium, high
    target_market: str  # TR, EU, US, Global
    recommended_niches: List[str]
    warnings: List[str]
    tips: List[str]


class TweetCredAnalyzer:
    """
    TweetCred ve Engagement Debt Analizi

    X algoritmasının gizli otorite skorlama sistemini simüle eder.
    """

    def calculate_tweetcred(
        self,
        profile: XProfile,
        avg_engagement_rate: float = 0.02,
        post_consistency: float = 0.5,
        niche_focus: float = 0.5
    ) -> TweetCredScore:
        """
        TweetCred skorunu hesaplar.

        Args:
            profile: X profil bilgileri
            avg_engagement_rate: Ortalama engagement oranı
            post_consistency: Post tutarlılığı (0-1)
            niche_focus: Niş odaklanma (0-1)

        Returns:
            TweetCredScore objesi
        """
        score = TweetCredScore()

        # Verified boost
        if profile.verified:
            score.verified_boost = TWEETCRED_VERIFIED_BOOST

        # Bio skoru (dolu ve kaliteli bio)
        if profile.description:
            bio_len = len(profile.description)
            if bio_len >= 100:
                score.bio_score = 15
            elif bio_len >= 50:
                score.bio_score = 10
            elif bio_len >= 20:
                score.bio_score = 5

        # Takip/Takipçi ratio skoru
        ratio = profile.follower_ratio
        if ratio >= 10:
            score.ratio_score = 30
        elif ratio >= 5:
            score.ratio_score = 20
        elif ratio >= 2:
            score.ratio_score = 15
        elif ratio >= 1:
            score.ratio_score = 10
        elif ratio >= 0.5:
            score.ratio_score = 5
        else:
            score.ratio_score = -10  # Çok düşük ratio penaltı

        # Engagement history skoru
        if avg_engagement_rate >= 0.05:
            score.engagement_history_score = 40
        elif avg_engagement_rate >= 0.03:
            score.engagement_history_score = 30
        elif avg_engagement_rate >= 0.02:
            score.engagement_history_score = 20
        elif avg_engagement_rate >= 0.01:
            score.engagement_history_score = 10
        elif avg_engagement_rate >= 0.005:
            score.engagement_history_score = 0
        else:
            score.engagement_history_score = -20  # Düşük engagement penaltı

        # Niş odaklanma skoru
        score.niche_focus_score = int(niche_focus * 30)

        # Hesap yaşı bonusu
        age_days = profile.account_age_days
        if age_days >= 365 * 3:  # 3+ yıl
            score.engagement_history_score += 15
        elif age_days >= 365:  # 1+ yıl
            score.engagement_history_score += 10
        elif age_days >= 180:  # 6+ ay
            score.engagement_history_score += 5

        return score

    def analyze_engagement_debt(
        self,
        posts: int,
        likes: int,
        impressions: int
    ) -> EngagementDebt:
        """
        Engagement debt analizi yapar.

        Args:
            posts: Toplam post sayısı
            likes: Toplam beğeni sayısı
            impressions: Toplam görüntülenme sayısı

        Returns:
            EngagementDebt objesi
        """
        debt = EngagementDebt(
            total_posts=posts,
            total_likes=likes,
            total_impressions=impressions
        )

        if debt.has_debt:
            # Borç seviyesini hesapla
            rate = debt.engagement_rate
            if rate < 0.001:
                debt.debt_level = 1.0
            elif rate < 0.003:
                debt.debt_level = 0.7
            else:
                debt.debt_level = 0.4

        return debt

    def get_monetization_analysis(
        self,
        profile: XProfile,
        niche: str,
        target_market: str = "TR"
    ) -> MonetizationAnalysis:
        """
        Monetization analizi yapar.

        Args:
            profile: Profil bilgileri
            niche: İçerik nişi
            target_market: Hedef pazar (TR, EU, US)

        Returns:
            MonetizationAnalysis objesi
        """
        warnings = []
        tips = []
        recommended_niches = []

        niche_lower = niche.lower()

        # RPM tahmini (1000 görüntülenme başına gelir)
        base_rpm = 0.5  # Base RPM (USD)

        # Market çarpanı
        market_multiplier = {
            "US": 3.0,
            "EU": 2.0,
            "TR": 0.3,  # Tier 3 ülke
            "Global": 1.5
        }.get(target_market, 1.0)

        # Niş çarpanı
        if any(n in niche_lower for n in ["crypto", "kripto", "borsa", "trading", "forex"]):
            niche_multiplier = 3.0
            niche_profitability = "high"
        elif any(n in niche_lower for n in ["finans", "banka", "yatırım", "fintech"]):
            niche_multiplier = 2.5
            niche_profitability = "high"
        elif any(n in niche_lower for n in ["bahis", "iddia", "casino"]):
            niche_multiplier = 2.0
            niche_profitability = "medium-high"
        elif any(n in niche_lower for n in ["tech", "yazılım", "ai", "startup"]):
            niche_multiplier = 1.5
            niche_profitability = "medium"
        elif any(n in niche_lower for n in ["e-ticaret", "pazaryeri", "alışveriş"]):
            niche_multiplier = 1.3
            niche_profitability = "medium"
        else:
            niche_multiplier = 0.8
            niche_profitability = "low"

        # Verified çarpanı
        verified_multiplier = 1.3 if profile.verified else 1.0

        # Final RPM
        estimated_rpm = base_rpm * market_multiplier * niche_multiplier * verified_multiplier

        # Uyarılar
        if target_market == "TR":
            warnings.append("Türkiye tier 3 ülke - RPM düşük")
            warnings.append("Yerli markaların reklam verdiği nişlere odaklan")
            recommended_niches = TR_PROFITABLE_NICHES[:5]
            tips.append("Finans, borsa, kripto nişlerinde içerik üret")
            tips.append("Bahis/iddia platformları TR'de yüksek reklam bütçesi harcıyor")

        if target_market in ["US", "EU"]:
            tips.append("Mention farm yapan hesaplar gibi strateji izle (@cb_doge örneği)")
            tips.append("İngilizce içerik = daha yüksek RPM")
            recommended_niches = GLOBAL_PROFITABLE_NICHES[:5]

        if not profile.verified:
            warnings.append("Mavi tik olmadan gelir potansiyeli sınırlı")
            tips.append("X Premium al - duplicate content detector'den %30 muafiyet")

        # Genel tavsiyeler
        tips.append("Mention'lara çekmeye odaklan - asıl gelir oradan")
        tips.append("Dwell time'ı artır - uzun okunabilir içerik")

        return MonetizationAnalysis(
            estimated_rpm=round(estimated_rpm, 2),
            niche_profitability=niche_profitability,
            target_market=target_market,
            recommended_niches=recommended_niches,
            warnings=warnings,
            tips=tips
        )

    def get_dwell_time_tips(self, tweet: str) -> List[str]:
        """Tweet için dwell time optimizasyon önerileri"""
        tips = []
        lines = tweet.count('\n')
        words = len(tweet.split())

        if words < 30:
            tips.append("Daha uzun içerik = daha fazla dwell time")

        if lines < 3:
            tips.append("Satır araları ekle - okuma süresini artırır")

        if '?' not in tweet:
            tips.append("Soru ekle - düşünme süresi = dwell time")

        if not any(c in tweet for c in ['1.', '2.', '•', '-', '→']):
            tips.append("Liste formatı kullan - taranabilir içerik dwell time artırır")

        if 'ama' not in tweet.lower() and 'ancak' not in tweet.lower() and 'fakat' not in tweet.lower():
            tips.append("Plot twist/karşıtlık ekle - merak uyandırır")

        return tips


class TweetScraper:
    """
    API gerektirmeden tweet çekme.
    Birden fazla yöntem dener: Syndication API, xcancel, Nitter alternatifleri.
    """

    # Çalışan alternatif instance'lar (Ocak 2025 güncel)
    # xcancel.com en güvenilir, diğerleri yedek
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
            'Upgrade-Insecure-Requests': '1',
        }

    def _decompress_response(self, response) -> str:
        """Response'u decompress et (gzip desteği)"""
        import gzip
        import io

        data = response.read()
        if response.info().get('Content-Encoding') == 'gzip':
            try:
                buf = io.BytesIO(data)
                with gzip.GzipFile(fileobj=buf) as f:
                    return f.read().decode('utf-8')
            except:
                pass
        return data.decode('utf-8', errors='ignore')

    def fetch_tweets_syndication(self, username: str, count: int = 50) -> List[Dict]:
        """
        Twitter Syndication API uzerinden tweet cek.
        Bu API herkese acik ve API key gerektirmiyor.
        """
        tweets = []
        try:
            # Twitter'in embed/syndication endpoint'i
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://twitter.com/',
                'Origin': 'https://twitter.com',
            }

            html = None

            # Requests kutuphanesi varsa onu kullan (daha guvenilir)
            if REQUESTS_AVAILABLE:
                try:
                    print(f"[Syndication] Fetching {url}")
                    resp = requests.get(url, headers=headers, timeout=30, verify=False)
                    print(f"[Syndication] Response status: {resp.status_code}, length: {len(resp.text)}")
                    resp.raise_for_status()
                    html = resp.text
                except Exception as req_err:
                    print(f"[Syndication] Requests failed: {req_err}")
                    # urllib fallback
                    try:
                        req = urllib.request.Request(url, headers=headers)
                        with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as response:
                            html = self._decompress_response(response)
                            print(f"[Syndication] urllib fallback success, length: {len(html)}")
                    except Exception as urllib_err:
                        print(f"[Syndication] urllib also failed: {urllib_err}")
            else:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as response:
                    html = self._decompress_response(response)
                    print(f"[Syndication] urllib success, length: {len(html)}")

            if not html:
                print("[Syndication] No HTML received")
                return []

            # JSON data'yi HTML icinden cikar
            # Syndication API HTML icinde JSON embed eder
            json_pattern = r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>'
            json_match = re.search(json_pattern, html, re.DOTALL)

            if json_match:
                print(f"[Syndication] Found __NEXT_DATA__ script tag")
                try:
                    data = json.loads(json_match.group(1))
                    timeline = data.get('props', {}).get('pageProps', {}).get('timeline', {})
                    entries = timeline.get('entries', [])
                    print(f"[Syndication] Found {len(entries)} entries in timeline")

                    for entry in entries[:count]:
                        content = entry.get('content', {})
                        tweet_data = content.get('tweet', {})

                        if tweet_data:
                            text = tweet_data.get('full_text', tweet_data.get('text', ''))
                            if text and len(text) > 10:
                                tweets.append({
                                    "text": text,
                                    "likes": tweet_data.get('favorite_count', 0),
                                    "retweets": tweet_data.get('retweet_count', 0),
                                    "replies": tweet_data.get('reply_count', 0),
                                    "impressions": tweet_data.get('view_count', 100)
                                })
                    print(f"[Syndication] Parsed {len(tweets)} tweets from JSON")
                except json.JSONDecodeError as je:
                    print(f"[Syndication] JSON decode error: {je}")
            else:
                print(f"[Syndication] No __NEXT_DATA__ found, trying alternative patterns")

            # Alternatif: HTML'den direkt parse et
            if not tweets:
                # Tweet text pattern
                tweet_pattern = r'data-tweet-id="[^"]*"[^>]*>.*?<p[^>]*class="[^"]*tweet-text[^"]*"[^>]*>(.*?)</p>'
                matches = re.findall(tweet_pattern, html, re.DOTALL | re.IGNORECASE)

                for match in matches[:count]:
                    text = re.sub(r'<[^>]+>', '', match)
                    text = text.strip()
                    if text and len(text) > 10:
                        tweets.append({
                            "text": text,
                            "likes": 0,
                            "retweets": 0,
                            "replies": 0,
                            "impressions": 100
                        })

            if tweets:
                self.working_method = "Syndication API"

        except Exception as e:
            print(f"Syndication API error: {e}")

        return tweets

    def _find_working_instance(self) -> Optional[str]:
        """Çalışan bir alternatif instance bul"""
        for instance in self.ALTERNATIVE_INSTANCES:
            try:
                url = f"https://{instance}/"
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=8, context=SSL_CONTEXT) as response:
                    if response.status == 200:
                        self.working_instance = instance
                        return instance
            except Exception as e:
                print(f"Instance {instance} failed: {e}")
                continue
        return None

    def fetch_tweets_xcancel(self, username: str, count: int = 50) -> List[Dict]:
        """
        xcancel.com üzerinden tweet çek (en güvenilir Nitter alternatifi).
        """
        tweets = []
        try:
            url = f"https://xcancel.com/{username}"

            # Requests kütüphanesi varsa onu kullan
            if REQUESTS_AVAILABLE:
                try:
                    resp = requests.get(url, headers=self.headers, timeout=20, verify=False)
                    resp.raise_for_status()
                    html = resp.text
                except Exception as req_err:
                    print(f"xcancel requests failed: {req_err}")
                    req = urllib.request.Request(url, headers=self.headers)
                    with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as response:
                        html = self._decompress_response(response)
            else:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as response:
                    html = self._decompress_response(response)

            # xcancel Nitter tabanlı, aynı HTML yapısını kullanıyor
            tweet_pattern = r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>'
            matches = re.findall(tweet_pattern, html, re.DOTALL)

            for match in matches[:count]:
                text = re.sub(r'<[^>]+>', '', match)
                text = text.strip()

                if text and len(text) > 10:
                    tweets.append({
                        "text": text,
                        "likes": 0,
                        "retweets": 0,
                        "replies": 0,
                        "impressions": 100
                    })

            if tweets:
                self.working_method = "xcancel.com"

        except Exception as e:
            print(f"xcancel fetch error: {e}")

        return tweets

    def fetch_tweets_nitter(self, username: str, count: int = 50) -> List[Dict]:
        """
        Nitter alternatifleri üzerinden tweet çek.
        """
        if not self.working_instance:
            self._find_working_instance()

        if not self.working_instance:
            return []

        tweets = []
        try:
            url = f"https://{self.working_instance}/{username}"
            req = urllib.request.Request(url, headers=self.headers)

            with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as response:
                html = self._decompress_response(response)

            # Tweet içeriklerini bul
            tweet_pattern = r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>'
            matches = re.findall(tweet_pattern, html, re.DOTALL)

            for match in matches[:count]:
                text = re.sub(r'<[^>]+>', '', match)
                text = text.strip()

                if text and len(text) > 10:
                    tweets.append({
                        "text": text,
                        "likes": 0,
                        "retweets": 0,
                        "replies": 0,
                        "impressions": 100
                    })

            if tweets:
                self.working_method = f"Nitter ({self.working_instance})"

        except Exception as e:
            print(f"Nitter fetch error: {e}")

        return tweets

    def fetch_tweets_rss(self, username: str, count: int = 50) -> List[Dict]:
        """
        RSS feed üzerinden tweet çek.
        """
        # Önce xcancel RSS dene
        rss_sources = [
            f"https://xcancel.com/{username}/rss",
        ]

        if self.working_instance:
            rss_sources.append(f"https://{self.working_instance}/{username}/rss")

        tweets = []
        for rss_url in rss_sources:
            try:
                req = urllib.request.Request(rss_url, headers=self.headers)

                with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as response:
                    xml = self._decompress_response(response)

                # RSS parsing
                item_pattern = r'<item>(.*?)</item>'
                items = re.findall(item_pattern, xml, re.DOTALL)

                for item in items[:count]:
                    desc_match = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
                    if desc_match:
                        text = desc_match.group(1)
                        text = re.sub(r'<!\[CDATA\[', '', text)
                        text = re.sub(r'\]\]>', '', text)
                        text = re.sub(r'<[^>]+>', '', text)
                        text = text.strip()

                        if text and len(text) > 10:
                            tweets.append({
                                "text": text,
                                "likes": 0,
                                "retweets": 0,
                                "replies": 0,
                                "impressions": 100
                            })

                if tweets:
                    self.working_method = "RSS Feed"
                    break

            except Exception as e:
                print(f"RSS fetch error ({rss_url}): {e}")
                continue

        return tweets

    def fetch_tweets_ntscraper(self, username: str, count: int = 50) -> List[Dict]:
        """
        ntscraper kütüphanesi ile tweet çek.
        Nitter instance'larını otomatik yönetir.
        """
        if not NTSCRAPER_AVAILABLE:
            return []

        tweets = []
        try:
            # ntscraper instance'ı oluştur
            scraper = Nitter(log_level=0, skip_instance_check=False)

            # Profil tweetlerini çek
            result = scraper.get_tweets(username, mode='user', number=count)

            if result and 'tweets' in result:
                for tweet in result['tweets'][:count]:
                    text = tweet.get('text', '')
                    if text and len(text) > 10:
                        tweets.append({
                            "text": text,
                            "likes": tweet.get('stats', {}).get('likes', 0),
                            "retweets": tweet.get('stats', {}).get('retweets', 0),
                            "replies": tweet.get('stats', {}).get('comments', 0),
                            "impressions": tweet.get('stats', {}).get('likes', 0) * 10 or 100
                        })

            if tweets:
                self.working_method = "ntscraper"

        except Exception as e:
            print(f"ntscraper error: {e}")

        return tweets

    def fetch_tweets(self, username: str, count: int = 50) -> List[Dict]:
        """
        Tweet çek - birden fazla yöntem dener.
        Sıra: Syndication API -> xcancel -> ntscraper -> RSS -> Nitter alternatifleri
        """
        # Kullanıcı adından @ işaretini kaldır
        username = username.lstrip('@').strip()
        errors = []

        # 1. Önce Twitter Syndication API dene (en güvenilir)
        print(f"[Scraper] Trying Syndication API for @{username}...")
        try:
            tweets = self.fetch_tweets_syndication(username, count)
            if tweets:
                print(f"[Scraper] [OK] Syndication API: {len(tweets)} tweets found")
                return tweets
            else:
                errors.append("Syndication API: No tweets returned")
        except Exception as e:
            errors.append(f"Syndication API: {str(e)}")
            print(f"[Scraper] Syndication API error: {e}")

        # 2. xcancel.com dene (en güvenilir Nitter alternatifi)
        print(f"[Scraper] Trying xcancel.com for @{username}...")
        try:
            tweets = self.fetch_tweets_xcancel(username, count)
            if tweets:
                print(f"[Scraper] [OK] xcancel.com: {len(tweets)} tweets found")
                return tweets
            else:
                errors.append("xcancel.com: No tweets returned")
        except Exception as e:
            errors.append(f"xcancel.com: {str(e)}")
            print(f"[Scraper] xcancel.com error: {e}")

        # 3. ntscraper dene (kendi Nitter instance yönetimi var)
        if NTSCRAPER_AVAILABLE:
            print(f"[Scraper] Trying ntscraper for @{username}...")
            try:
                tweets = self.fetch_tweets_ntscraper(username, count)
                if tweets:
                    print(f"[Scraper] [OK] ntscraper: {len(tweets)} tweets found")
                    return tweets
                else:
                    errors.append("ntscraper: No tweets returned")
            except Exception as e:
                errors.append(f"ntscraper: {str(e)}")
                print(f"[Scraper] ntscraper error: {e}")

        # 4. RSS feed dene
        print(f"[Scraper] Trying RSS feeds for @{username}...")
        try:
            tweets = self.fetch_tweets_rss(username, count)
            if tweets:
                print(f"[Scraper] [OK] RSS: {len(tweets)} tweets found")
                return tweets
            else:
                errors.append("RSS: No tweets returned")
        except Exception as e:
            errors.append(f"RSS: {str(e)}")
            print(f"[Scraper] RSS error: {e}")

        # 5. Son çare: diğer Nitter alternatifleri
        print(f"[Scraper] Trying Nitter alternatives for @{username}...")
        try:
            tweets = self.fetch_tweets_nitter(username, count)
            if tweets:
                print(f"[Scraper] [OK] Nitter: {len(tweets)} tweets found")
                return tweets
            else:
                errors.append("Nitter: No tweets returned")
        except Exception as e:
            errors.append(f"Nitter: {str(e)}")
            print(f"[Scraper] Nitter error: {e}")

        print(f"[Scraper] [FAIL] Could not fetch tweets for @{username}")
        print(f"[Scraper] Errors: {'; '.join(errors)}")
        self.last_errors = errors
        return []

    def get_status(self) -> Dict:
        """Scraper durumunu döndür"""
        # Tüm yöntemleri test et
        methods_status = []

        # Syndication API test
        try:
            url = "https://syndication.twitter.com/"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=5, context=SSL_CONTEXT) as response:
                if response.status == 200:
                    methods_status.append("Syndication API [OK]")
        except:
            methods_status.append("Syndication API [FAIL]")

        # xcancel test
        try:
            url = "https://xcancel.com/"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=5, context=SSL_CONTEXT) as response:
                if response.status == 200:
                    methods_status.append("xcancel.com [OK]")
        except:
            methods_status.append("xcancel.com [FAIL]")

        # ntscraper test
        if NTSCRAPER_AVAILABLE:
            try:
                scraper = Nitter(log_level=0, skip_instance_check=True)
                methods_status.append("ntscraper [OK]")
            except:
                methods_status.append("ntscraper [FAIL]")
        else:
            methods_status.append("ntscraper (not installed)")

        # Nitter alternatifleri test
        instance = self._find_working_instance()
        if instance:
            methods_status.append(f"Nitter ({instance}) [OK]")
        else:
            methods_status.append("Nitter alternatifleri [FAIL]")

        working = any("[OK]" in m for m in methods_status)

        return {
            "working": working,
            "instance": self.working_instance,
            "method": self.working_method or "Multiple methods available",
            "methods_status": methods_status
        }


@dataclass
class TweetStyleAnalysis:
    """Kullanıcının tweet stil analizi"""
    avg_length: float = 0
    avg_line_breaks: float = 0
    emoji_frequency: float = 0  # emoji per tweet
    question_frequency: float = 0  # soru işareti kullanan tweet oranı
    hashtag_frequency: float = 0
    mention_frequency: float = 0
    link_frequency: float = 0
    common_words: List[str] = None
    common_emojis: List[str] = None
    tone: str = "neutral"  # professional, casual, provocative, educational
    topics: List[str] = None
    best_performing_patterns: List[str] = None
    avg_engagement_rate: float = 0
    posting_hours: List[int] = None  # en aktif saatler

    def __post_init__(self):
        if self.common_words is None:
            self.common_words = []
        if self.common_emojis is None:
            self.common_emojis = []
        if self.topics is None:
            self.topics = []
        if self.best_performing_patterns is None:
            self.best_performing_patterns = []
        if self.posting_hours is None:
            self.posting_hours = []


class TweetStyleAnalyzer:
    """Kullanıcının tweetlerini analiz edip stil çıkarır"""

    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )

    def analyze_tweets(self, tweets: List[Dict]) -> TweetStyleAnalysis:
        """
        Tweet listesini analiz edip stil çıkarır.

        Args:
            tweets: Tweet listesi [{"text": "...", "likes": 10, "retweets": 5, "replies": 2, "impressions": 1000}, ...]

        Returns:
            TweetStyleAnalysis objesi
        """
        if not tweets:
            return TweetStyleAnalysis()

        analysis = TweetStyleAnalysis()

        total_length = 0
        total_line_breaks = 0
        total_emojis = 0
        total_questions = 0
        total_hashtags = 0
        total_mentions = 0
        total_links = 0
        all_emojis = []
        all_words = []
        engagement_rates = []

        for tweet in tweets:
            text = tweet.get("text", "")

            # Uzunluk
            total_length += len(text)

            # Satır araları
            total_line_breaks += text.count('\n')

            # Emojiler
            emojis = self.EMOJI_PATTERN.findall(text)
            total_emojis += len(emojis)
            all_emojis.extend(emojis)

            # Soru işareti
            if '?' in text:
                total_questions += 1

            # Hashtag
            hashtags = re.findall(r'#\w+', text)
            total_hashtags += len(hashtags)

            # Mention
            mentions = re.findall(r'@\w+', text)
            total_mentions += len(mentions)

            # Link
            if 'http' in text or 't.co' in text:
                total_links += 1

            # Kelimeler (stopword'ler hariç)
            words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]{4,}\b', text.lower())
            all_words.extend(words)

            # Engagement rate
            impressions = tweet.get("impressions", 0)
            if impressions > 0:
                likes = tweet.get("likes", 0)
                retweets = tweet.get("retweets", 0)
                replies = tweet.get("replies", 0)
                engagement = (likes + retweets * 2 + replies * 1.5) / impressions
                engagement_rates.append(engagement)

        n = len(tweets)

        analysis.avg_length = total_length / n
        analysis.avg_line_breaks = total_line_breaks / n
        analysis.emoji_frequency = total_emojis / n
        analysis.question_frequency = total_questions / n
        analysis.hashtag_frequency = total_hashtags / n
        analysis.mention_frequency = total_mentions / n
        analysis.link_frequency = total_links / n

        # En sık kullanılan emojiler
        if all_emojis:
            emoji_counts = {}
            for e in all_emojis:
                emoji_counts[e] = emoji_counts.get(e, 0) + 1
            analysis.common_emojis = sorted(emoji_counts.keys(), key=lambda x: emoji_counts[x], reverse=True)[:5]

        # En sık kullanılan kelimeler (stopword'ler hariç)
        stopwords = {'için', 'olan', 'gibi', 'daha', 'çok', 'kadar', 'nasıl', 'neden', 'this', 'that', 'with', 'from', 'have', 'been', 'will', 'your', 'they', 'what', 'when', 'there'}
        filtered_words = [w for w in all_words if w not in stopwords]
        if filtered_words:
            word_counts = {}
            for w in filtered_words:
                word_counts[w] = word_counts.get(w, 0) + 1
            analysis.common_words = sorted(word_counts.keys(), key=lambda x: word_counts[x], reverse=True)[:10]

        # Ortalama engagement
        if engagement_rates:
            analysis.avg_engagement_rate = sum(engagement_rates) / len(engagement_rates)

        # Ton tahmini
        analysis.tone = self._detect_tone(tweets)

        return analysis

    def _detect_tone(self, tweets: List[Dict]) -> str:
        """Tweet'lerden ton tespit et"""
        texts = " ".join([t.get("text", "") for t in tweets]).lower()

        provocative_words = ['tartışmalı', 'yanlış', 'hata', 'aslında', 'unpopular', 'controversial', 'wrong', 'mistake']
        educational_words = ['öğrendim', 'ipucu', 'rehber', 'nasıl', 'adım', 'learned', 'tips', 'guide', 'how to', 'step']
        casual_words = ['haha', 'lol', 'sjsj', 'random', 'wtf', 'omg']
        professional_words = ['analiz', 'strateji', 'veri', 'rapor', 'analysis', 'strategy', 'data', 'report']

        scores = {
            'provocative': sum(1 for w in provocative_words if w in texts),
            'educational': sum(1 for w in educational_words if w in texts),
            'casual': sum(1 for w in casual_words if w in texts),
            'professional': sum(1 for w in professional_words if w in texts)
        }

        if max(scores.values()) == 0:
            return "neutral"
        return max(scores, key=scores.get)

    def generate_style_prompt(self, analysis: TweetStyleAnalysis) -> str:
        """Stil analizinden AI prompt'u oluştur"""
        prompt_parts = []

        prompt_parts.append("BU KULLANICININ STİLİNE UYGUN TWEET YAZMALSIN:")

        # Uzunluk
        if analysis.avg_length < 100:
            prompt_parts.append("- Kısa ve öz tweetler tercih ediyor")
        elif analysis.avg_length < 300:
            prompt_parts.append("- Orta uzunlukta tweetler yazıyor")
        else:
            prompt_parts.append("- Uzun, detaylı tweetler yazıyor")

        # Satır araları
        if analysis.avg_line_breaks >= 2:
            prompt_parts.append("- Satır araları kullanıyor (okunabilirlik için)")
        else:
            prompt_parts.append("- Genellikle tek paragraf yazıyor")

        # Emoji
        if analysis.emoji_frequency >= 2:
            prompt_parts.append(f"- Emoji seven biri: {' '.join(analysis.common_emojis[:3]) if analysis.common_emojis else '🔥'}")
        elif analysis.emoji_frequency >= 0.5:
            prompt_parts.append("- Ara sıra emoji kullanıyor")
        else:
            prompt_parts.append("- Emoji kullanmıyor veya çok az")

        # Soru
        if analysis.question_frequency >= 0.3:
            prompt_parts.append("- Sıklıkla soru soruyor (etkileşim odaklı)")

        # Ton
        tone_desc = {
            'provocative': "- Provokatif ve tartışmacı ton",
            'educational': "- Eğitici ve bilgi paylaşan ton",
            'casual': "- Rahat ve eğlenceli ton",
            'professional': "- Profesyonel ve ciddi ton",
            'neutral': "- Nötr ve dengeli ton"
        }
        prompt_parts.append(tone_desc.get(analysis.tone, "- Nötr ton"))

        # Sık kullanılan kelimeler
        if analysis.common_words:
            prompt_parts.append(f"- Sık kullandığı kelimeler: {', '.join(analysis.common_words[:5])}")

        return "\n".join(prompt_parts)


class XProfileAnalyzer:
    """X Profil analizi ve API entegrasyonu"""

    # Takipçi sayısına göre engagement çarpanları
    TIER_MULTIPLIERS = {
        "mega": 0.5,      # 1M+ - düşük engagement rate ama yüksek reach
        "macro": 0.7,     # 100K+
        "mid": 1.0,       # 10K+ - optimal
        "micro": 1.3,     # 1K+ - yüksek engagement rate
        "nano": 1.5,      # 100+ - çok yüksek engagement
        "starter": 0.8    # <100 - düşük reach
    }

    def __init__(self, bearer_token: Optional[str] = None):
        """
        Args:
            bearer_token: X API Bearer Token
        """
        self.bearer_token = bearer_token or os.environ.get("X_BEARER_TOKEN")
        self.client = None

        if TWEEPY_AVAILABLE and self.bearer_token:
            self.client = tweepy.Client(bearer_token=self.bearer_token)

    def get_profile(self, username: str) -> Optional[XProfile]:
        """
        Kullanıcı profilini çeker.

        Args:
            username: X kullanıcı adı (@olmadan)

        Returns:
            XProfile objesi veya None
        """
        if not self.client:
            return None

        try:
            user = self.client.get_user(
                username=username,
                user_fields=[
                    "created_at", "description", "public_metrics",
                    "profile_image_url", "verified"
                ]
            )

            if user.data:
                return XProfile(
                    username=user.data.username,
                    name=user.data.name,
                    followers_count=user.data.public_metrics["followers_count"],
                    following_count=user.data.public_metrics["following_count"],
                    tweet_count=user.data.public_metrics["tweet_count"],
                    created_at=str(user.data.created_at),
                    verified=getattr(user.data, 'verified', False),
                    description=user.data.description or "",
                    profile_image_url=user.data.profile_image_url or ""
                )
        except Exception as e:
            print(f"Profil çekme hatası: {e}")

        return None

    def analyze_profile(self, profile: XProfile) -> Dict:
        """
        Profili analiz eder ve engagement faktörleri hesaplar.

        Args:
            profile: XProfile objesi

        Returns:
            Analiz sonuçları
        """
        analysis = {
            "tier": profile.engagement_tier,
            "tier_multiplier": self.TIER_MULTIPLIERS[profile.engagement_tier],
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
            "metrics": {}
        }

        # Takipçi sayısı analizi
        if profile.followers_count >= 10000:
            analysis["strengths"].append(f"Güçlü takipçi tabanı: {profile.followers_count:,}")
        elif profile.followers_count < 100:
            analysis["weaknesses"].append("Düşük takipçi sayısı - reach sınırlı")
            analysis["suggestions"].append("Tutarlı içerik ve etkileşim ile takipçi artırın")

        # Takipçi/Takip oranı
        ratio = profile.follower_ratio
        if ratio >= 2:
            analysis["strengths"].append(f"Yüksek takipçi oranı: {ratio:.1f}x")
        elif ratio < 0.5:
            analysis["weaknesses"].append("Düşük takipçi oranı - otorite sorgulanabilir")

        # Hesap yaşı
        age_days = profile.account_age_days
        if age_days >= 365:
            years = age_days // 365
            analysis["strengths"].append(f"Yerleşik hesap: {years}+ yıl")
        elif age_days < 90:
            analysis["weaknesses"].append("Yeni hesap - güven inşası gerekli")
            analysis["suggestions"].append("Düzenli paylaşım yaparak güven oluşturun")

        # Tweet sayısı
        if profile.tweet_count >= 1000:
            analysis["strengths"].append("Aktif içerik üretici")
        elif profile.tweet_count < 50:
            analysis["suggestions"].append("Daha fazla içerik üretin")

        # Verified badge
        if profile.verified:
            analysis["strengths"].append("Doğrulanmış hesap [OK]")
            analysis["tier_multiplier"] *= 1.2

        # Metrikleri kaydet
        analysis["metrics"] = {
            "followers": profile.followers_count,
            "following": profile.following_count,
            "tweets": profile.tweet_count,
            "ratio": round(ratio, 2),
            "age_days": age_days,
            "verified": profile.verified
        }

        return analysis

    def calculate_reach_prediction(
        self,
        profile: XProfile,
        tweet_score: float,
        posting_hour: Optional[int] = None,
        posting_day: Optional[int] = None,
        content_type: str = "text_only",
        has_trending_hashtag: bool = False,
        tweetcred_score: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Gerçekçi reach tahmini hesaplar.

        Faktörler:
        - Takipçi sayısı ve tier
        - Tweet kalite skoru
        - Posting zamanı (saat ve gün)
        - İçerik tipi (media, thread, vb.)
        - TweetCred skoru (hesap otoritesi)
        - Viral potansiyel

        Args:
            profile: XProfile objesi
            tweet_score: Tweet analiz skoru (0-100)
            posting_hour: Tweet atılacak saat (0-23, None = şu anki saat)
            posting_day: Tweet atılacak gün (0=Pazartesi, 6=Pazar, None = bugün)
            content_type: İçerik tipi (text_only, with_image, with_video, vb.)
            has_trending_hashtag: Trend hashtag kullanılıyor mu
            tweetcred_score: TweetCred skoru (None = tahmin et)

        Returns:
            Detaylı reach tahmini
        """
        from datetime import datetime

        # Varsayılan değerler
        now = datetime.now()
        if posting_hour is None:
            posting_hour = now.hour
        if posting_day is None:
            posting_day = now.weekday()

        # ============ BASE REACH HESAPLAMA ============
        base_followers = profile.followers_count

        # X algoritması: Organik reach = takipçilerin %5-15'i (tier'a bağlı)
        organic_reach_rate = {
            "mega": 0.03,     # 1M+ hesaplar sadece %3
            "macro": 0.05,    # 100K+ %5
            "mid": 0.08,      # 10K+ %8
            "micro": 0.12,    # 1K+ %12
            "nano": 0.15,     # 100+ %15
            "starter": 0.20   # <100 %20 (ama düşük sayılar)
        }

        base_organic_rate = organic_reach_rate.get(profile.engagement_tier, 0.10)
        base_reach = int(base_followers * base_organic_rate)

        # ============ MULTIPLIER'LAR ============

        # 1. Tweet kalite skoru (0-100 -> 0.5-1.5 multiplier)
        quality_mult = 0.5 + (tweet_score / 100)

        # 2. Saat multiplier'ı
        hour_mult = HOURLY_ENGAGEMENT_MULTIPLIERS.get(posting_hour, 1.0)

        # 3. Gün multiplier'ı
        day_mult = DAILY_ENGAGEMENT_MULTIPLIERS.get(posting_day, 1.0)

        # 4. İçerik tipi multiplier'ı
        content_mult = CONTENT_TYPE_MULTIPLIERS.get(content_type, 1.0)

        # 5. TweetCred multiplier (hesap otoritesi)
        if tweetcred_score is None:
            # Basit tahmin: verified +50, takipçi oranına göre +/-
            estimated_cred = -128 + (100 if profile.verified else 0)
            if profile.follower_ratio > 2:
                estimated_cred += 30
            if profile.tweet_count > 1000:
                estimated_cred += 20
            tweetcred_score = estimated_cred

        # TweetCred -> multiplier dönüşümü
        if tweetcred_score >= 50:
            cred_mult = 1.5
        elif tweetcred_score >= 17:
            cred_mult = 1.0
        elif tweetcred_score >= -50:
            cred_mult = 0.5
        else:
            cred_mult = 0.1  # Cold start suppression

        # 6. Viral potansiyel
        viral_mult = 1.0
        if has_trending_hashtag:
            viral_mult *= VIRAL_FACTORS.get("trending_hashtag", 2.0)

        # ============ TOPLAM REACH HESAPLAMA ============

        # Tüm multiplier'ları birleştir
        total_mult = quality_mult * hour_mult * day_mult * content_mult * cred_mult * viral_mult

        # Algoritmik boost potansiyeli (For You'da görünme)
        # Yüksek engagement ilk 30 dakikada -> boost
        foryou_boost = 1.0
        if total_mult > 1.5:
            foryou_boost = 1.5  # For You'da görünme şansı
        elif total_mult > 1.2:
            foryou_boost = 1.2

        # Final impressions
        impressions = int(base_reach * total_mult * foryou_boost)

        # Minimum 10, maksimum takipçi * 10 (viral limit)
        impressions = max(10, min(impressions, base_followers * 10))

        # ============ ENGAGEMENT TAHMİNİ ============

        # Base engagement rate (tier'a göre)
        tier_engagement_rate = {
            "mega": 0.01,     # %1
            "macro": 0.02,    # %2
            "mid": 0.03,      # %3
            "micro": 0.05,    # %5
            "nano": 0.08,     # %8
            "starter": 0.10   # %10
        }

        base_eng_rate = tier_engagement_rate.get(profile.engagement_tier, 0.03)

        # Kalite ve zamanlamaya göre engagement artışı
        adjusted_eng_rate = base_eng_rate * (quality_mult * 0.7 + 0.3)

        engagements = int(impressions * adjusted_eng_rate)

        # Engagement dağılımı (X algorithm analytics'e dayalı)
        likes = int(engagements * 0.55)           # %55 like
        retweets = int(engagements * 0.08)        # %8 retweet
        replies = int(engagements * 0.12)         # %12 reply
        bookmarks = int(engagements * 0.15)       # %15 bookmark
        quotes = int(engagements * 0.03)          # %3 quote
        profile_visits = int(engagements * 0.07)  # %7 profil ziyareti

        # ============ ZAMANLAMA ANALİZİ ============

        # Optimal saat kontrolü
        optimal_score = int(hour_mult * day_mult * 50)  # 0-100 arası

        if hour_mult >= 1.3:
            timing_quality = "Mukemmel"
        elif hour_mult >= 1.0:
            timing_quality = "Iyi"
        elif hour_mult >= 0.7:
            timing_quality = "Orta"
        else:
            timing_quality = "Zayif"

        # En iyi alternatif saatler
        best_hours = sorted(
            HOURLY_ENGAGEMENT_MULTIPLIERS.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        return {
            # Temel metrikler
            "impressions": impressions,
            "engagements": engagements,
            "likes": likes,
            "retweets": retweets,
            "replies": replies,
            "bookmarks": bookmarks,
            "quotes": quotes,
            "profile_visits": profile_visits,
            "engagement_rate": round((engagements / max(impressions, 1)) * 100, 2),

            # Multiplier detayları
            "multipliers": {
                "quality": round(quality_mult, 2),
                "hour": round(hour_mult, 2),
                "day": round(day_mult, 2),
                "content": round(content_mult, 2),
                "tweetcred": round(cred_mult, 2),
                "viral": round(viral_mult, 2),
                "foryou_boost": round(foryou_boost, 2),
                "total": round(total_mult * foryou_boost, 2)
            },

            # Zamanlama analizi
            "timing": {
                "posting_hour": posting_hour,
                "posting_day": posting_day,
                "quality": timing_quality,
                "score": optimal_score,
                "best_hours": [{"hour": h, "multiplier": m} for h, m in best_hours]
            },

            # Reach aralığı (min-max tahmini)
            "reach_range": {
                "pessimistic": int(impressions * 0.5),
                "expected": impressions,
                "optimistic": int(impressions * 2.0),
                "viral_potential": int(impressions * 5.0) if viral_mult > 1 else None
            },

            # Hesap bilgisi
            "account": {
                "tier": profile.engagement_tier,
                "tweetcred_estimate": tweetcred_score,
                "organic_reach_rate": f"{base_organic_rate*100:.1f}%"
            }
        }

    def get_optimal_posting_times(self, timezone: str = "TR") -> Dict[str, any]:
        """
        Optimal tweet atma zamanlarini dondurur.

        Args:
            timezone: Saat dilimi (TR = Turkiye UTC+3)

        Returns:
            Optimal zamanlar ve onerileri
        """
        from datetime import datetime

        now = datetime.now()
        current_hour = now.hour
        current_day = now.weekday()

        # En iyi saatler
        sorted_hours = sorted(
            HOURLY_ENGAGEMENT_MULTIPLIERS.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_hours = sorted_hours[:5]  # En iyi 5 saat
        worst_hours = sorted_hours[-5:]  # En kotu 5 saat

        # En iyi gunler
        sorted_days = sorted(
            DAILY_ENGAGEMENT_MULTIPLIERS.items(),
            key=lambda x: x[1],
            reverse=True
        )

        day_names = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]

        # Simdi icin skor
        current_score = (
            HOURLY_ENGAGEMENT_MULTIPLIERS.get(current_hour, 1.0) *
            DAILY_ENGAGEMENT_MULTIPLIERS.get(current_day, 1.0)
        )

        # Bugunun kalan saatleri icin en iyi zaman
        best_remaining_hour = None
        best_remaining_mult = 0
        for hour in range(current_hour + 1, 24):
            mult = HOURLY_ENGAGEMENT_MULTIPLIERS.get(hour, 1.0)
            if mult > best_remaining_mult:
                best_remaining_mult = mult
                best_remaining_hour = hour

        # Oneri olustur
        if current_score >= 1.3:
            recommendation = "Simdi mukemmel bir zaman! Hemen tweetle."
        elif current_score >= 1.0:
            recommendation = "Simdi iyi bir zaman. Tweetleyebilirsin."
        elif best_remaining_hour:
            recommendation = f"Bekle! Bugun saat {best_remaining_hour:02d}:00'da daha iyi (x{best_remaining_mult:.1f})."
        else:
            recommendation = "Yarin sabah 09:00-12:00 arasi daha iyi olur."

        return {
            "current": {
                "hour": current_hour,
                "day": day_names[current_day],
                "score": round(current_score * 50, 0),  # 0-100 arasi
                "multiplier": round(current_score, 2)
            },
            "recommendation": recommendation,
            "best_hours": [
                {
                    "hour": h,
                    "time": f"{h:02d}:00",
                    "multiplier": round(m, 2),
                    "label": "Prime Time" if m >= 1.3 else "Iyi" if m >= 1.0 else "Normal"
                }
                for h, m in top_hours
            ],
            "worst_hours": [
                {
                    "hour": h,
                    "time": f"{h:02d}:00",
                    "multiplier": round(m, 2)
                }
                for h, m in worst_hours
            ],
            "best_days": [
                {
                    "day": d,
                    "name": day_names[d],
                    "multiplier": round(m, 2)
                }
                for d, m in sorted_days[:3]
            ],
            "optimal_slots": OPTIMAL_POSTING_HOURS_TR,
            "today_remaining_best": {
                "hour": best_remaining_hour,
                "time": f"{best_remaining_hour:02d}:00" if best_remaining_hour else None,
                "multiplier": round(best_remaining_mult, 2) if best_remaining_hour else None
            } if best_remaining_hour else None
        }

    def create_manual_profile(
        self,
        username: str,
        followers: int,
        following: int = 0,
        tweets: int = 0,
        verified: bool = False,
        account_age_years: float = 1
    ) -> XProfile:
        """
        API olmadan manuel profil oluşturur.

        Args:
            username: Kullanıcı adı
            followers: Takipçi sayısı
            following: Takip sayısı
            tweets: Tweet sayısı
            verified: Doğrulanmış mı
            account_age_years: Hesap yaşı (yıl)

        Returns:
            XProfile objesi
        """
        from datetime import datetime, timedelta

        created_date = datetime.now() - timedelta(days=int(account_age_years * 365))

        return XProfile(
            username=username,
            name=username,
            followers_count=followers,
            following_count=following,
            tweet_count=tweets,
            created_at=created_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            verified=verified,
            description=""
        )


@dataclass
class TweetTemplate:
    """Tweet şablonu"""
    name: str
    template: str
    description: str
    engagement_boost: float
    category: str = "general"


class XAlgorithmTweetGenerator:
    """
    X Algoritması tabanlı Tweet Generator

    For You feed'inde görünürlüğü artırmak için
    algoritmanın favori ettiği özellikleri kullanır.
    """

    # ============================================================================
    # X ALGORİTMASI ENGAGEMENT FAKTÖRLER (Phoenix WeightedScorer analizi)
    # ============================================================================

    # Engagement artıran faktörler (X algoritması ağırlıklarına göre)
    ENGAGEMENT_BOOSTERS = {
        # Reply tetikleyiciler (en değerli - 1.0 ağırlık)
        "question": 1.35,               # Soru = Reply olasılığı yüksek
        "call_to_action": 1.30,         # CTA = Share + Reply tetikler
        "controversy": 1.40,            # Tartışmalı = Yüksek engagement

        # Storytelling & Thread (Quote ve RT tetikler - 1.0 ağırlık)
        "storytelling": 1.25,           # Hikaye = Dwell time artırır
        "thread_hook": 1.45,            # Thread = Follow tetikler (4.0 ağırlık!)

        # Visual content (Photo expand - 0.5 ağırlık)
        "visual_content": 1.20,         # Görsel = Dwell + Expand

        # Profile click tetikleyiciler (1.0 ağırlık)
        "personal_experience": 1.25,    # Kişisel hikaye = Profile click
        "authority_signal": 1.30,       # Otorite gösterimi = Follow

        # Timely content
        "timely_topic": 1.25,           # Güncel konu = Keşfet görünürlüğü

        # Data & Insight
        "data_insight": 1.20,           # Veri = Bookmark (share_via_copy)

        # Formatting
        "emoji_moderate": 1.10,         # 1-5 emoji = Dikkat çekici
        "line_breaks": 1.15,            # Format = Dwell time
        "long_form_value": 1.25,        # Uzun içerik = Değerli

        # Share tetikleyiciler (1.0-1.5 ağırlık)
        "shareable_insight": 1.35,      # Paylaşılabilir içgörü
        "quotable_line": 1.30,          # Alıntılanabilir cümle
    }

    # Engagement düşüren faktörler (Negatif sinyaller - X algoritması)
    ENGAGEMENT_PENALTIES = {
        # Kritik cezalar (algoritma direkt bastırır)
        "external_link": 0.50,          # Dış link = %50 düşüş (ciddi ceza)
        "spam_keywords": 0.30,          # Spam = %70 düşüş

        # Orta cezalar
        "too_many_hashtags": 0.70,      # 3+ hashtag = Spam görünümü
        "all_caps": 0.75,               # Büyük harf = Agresif
        "emoji_overload": 0.80,         # 10+ emoji = Spam
        "no_engagement_hook": 0.85,     # Hook yok = Düşük etkileşim

        # Hafif cezalar
        "repetitive_content": 0.90,     # Tekrar = Düşük değer
        "low_effort": 0.85,             # Az emek = Düşük kalite

        # Negatif sinyal tetikleyiciler (block/mute/report riski)
        "aggressive_tone": 0.70,        # Saldırgan ton = Block riski
        "misleading_content": 0.60,     # Yanıltıcı = Report riski
    }

    # Phoenix Multi-Action Prediction Ağırlıkları
    # (X'in gerçek weighted scorer'ından)
    PHOENIX_WEIGHTS = {
        "favorite": 0.5,
        "reply": 1.0,
        "retweet": 1.0,
        "quote": 1.0,
        "click": 0.5,
        "profile_click": 1.0,
        "photo_expand": 0.5,
        "video_quality_view": 0.3,
        "share": 1.0,
        "share_via_dm": 1.5,
        "share_via_copy_link": 1.0,
        "dwell": 0.25,
        "dwell_time_continuous": 0.1,
        "follow_author": 4.0,  # En yüksek!
        # Negatif
        "not_interested": -1.0,
        "block_author": -1.0,
        "mute_author": -1.0,
        "report": -1.0,
    }

    # Genişletilmiş viral tweet şablonları
    TEMPLATES: List[TweetTemplate] = [
        # Thread & Hook şablonları
        TweetTemplate(
            name="thread_epic",
            template="""🧵 {konu} hakkında kimsenin anlatmadığı gerçekler:

Yıllardır bu alanda çalışıyorum ve gördüklerim sizi şaşırtacak.

Hazırsanız başlıyoruz 👇""",
            description="Epik thread açılışı",
            engagement_boost=1.45,
            category="thread"
        ),
        TweetTemplate(
            name="contrarian_take",
            template="""Herkes {yaygin_inanc} diyor.

Ben tam tersini düşünüyorum.

İşte nedeni:

{neden}

Unpopular opinion ama arkasındayım.""",
            description="Karşıt görüş - tartışma başlatıcı",
            engagement_boost=1.5,
            category="opinion"
        ),
        TweetTemplate(
            name="failure_story",
            template="""En büyük başarısızlığım:

{basarisizlik}

O gün öğrendiğim şey hayatımı değiştirdi:

{ogrenilen}

Başarısızlık en iyi öğretmen.""",
            description="Başarısızlık hikayesi - özgün ve güçlü",
            engagement_boost=1.4,
            category="story"
        ),
        TweetTemplate(
            name="hot_prediction",
            template="""Tahminim:

{tahmin}

6 ay içinde herkes bundan bahsedecek.

Screenshot alın. 📸""",
            description="Cesur tahmin",
            engagement_boost=1.35,
            category="prediction"
        ),
        TweetTemplate(
            name="myth_destruction",
            template=""""{mit}"

Bu cümleyi duymaktan bıktım.

Gerçek şu:

{gercek}

Kanıt mı? {kanit}""",
            description="Mit yıkıcı - agresif",
            engagement_boost=1.4,
            category="education"
        ),
        TweetTemplate(
            name="raw_honesty",
            template="""Bunu söylemek zor ama:

{itiraf}

Uzun süre bununla yaşadım.

Artık değil.

{cozum}""",
            description="Ham dürüstlük - duygusal bağ",
            engagement_boost=1.35,
            category="personal"
        ),
        TweetTemplate(
            name="framework_reveal",
            template="""10 yılda öğrendiğim {konu} framework'ü:

1️⃣ {adim1}
2️⃣ {adim2}
3️⃣ {adim3}
4️⃣ {adim4}
5️⃣ {adim5}

Bu sistemi uygulayan herkes sonuç alıyor.

Kaydet. Uygula. Sonuç al.""",
            description="Framework/sistem paylaşımı",
            engagement_boost=1.3,
            category="education"
        ),
        TweetTemplate(
            name="behind_scenes",
            template="""Kimsenin görmediği taraf:

{gorunmeyen}

Herkes sonucu görüyor.
Kimse süreci sormuyor.

İşte gerçek:

{gercek}""",
            description="Perde arkası - şeffaflık",
            engagement_boost=1.35,
            category="personal"
        ),
        TweetTemplate(
            name="question_bomb",
            template="""{soru}

Cevabı bildiğinizi sanıyorsunuz ama...

Gerçek cevap sizi şaşırtacak.

(Yorumlarda tahminlerinizi bekliyorum)""",
            description="Soru bombası - merak uyandırıcı",
            engagement_boost=1.4,
            category="engagement"
        ),
        TweetTemplate(
            name="comparison_shock",
            template="""{eski_yontem} → Geçmişte kaldı

{yeni_yontem} → Yeni standart

Hâlâ eski yöntemle devam edenler:

Bu değişimi kaçırmayın.

İşte neden: {neden}""",
            description="Karşılaştırma şoku",
            engagement_boost=1.3,
            category="education"
        ),
        TweetTemplate(
            name="long_form_story",
            template="""Bir hikaye anlatacağım.

{yil} yılında, {durum} içindeydim.

{olay1}

Sonra beklenmedik bir şey oldu:

{olay2}

Bu an her şeyi değiştirdi.

{sonuc}

Öğrendiğim en önemli şey:

{ders}

Bu hikayeyi paylaşmamın nedeni:

{neden}

Eğer sen de benzer bir durumda hissediyorsan, bil ki:

{mesaj}

---

Bu post'u kaydet.
İhtiyacın olduğunda tekrar oku.

Ve eğer tanıdığın biri varsa bu durumda, paylaş.

Birlikte daha güçlüyüz. 💪""",
            description="Uzun form hikaye - X Premium için",
            engagement_boost=1.5,
            category="long_form"
        ),
        TweetTemplate(
            name="expertise_dump",
            template="""Son {sure} yılda {alan} alanında öğrendiğim her şey:

📌 TEMEL PRENSİPLER:
• {prensip1}
• {prensip2}
• {prensip3}

🔧 PRATİK TAKTİKLER:
• {taktik1}
• {taktik2}
• {taktik3}

⚠️ YAPILMAMASI GEREKENLER:
• {hata1}
• {hata2}
• {hata3}

🎯 SONUÇ:
{sonuc}

Bu post'u bookmark'la.
{alan} ile ilgili tek rehber bu olsun.

Sorularınız varsa yorumlarda buluşalım. 👇""",
            description="Uzmanlık dökümü - değer dolu",
            engagement_boost=1.45,
            category="long_form"
        ),
        TweetTemplate(
            name="reality_check",
            template="""Gerçeklik kontrolü:

❌ {yanlis1}
❌ {yanlis2}
❌ {yanlis3}

✅ Gerçek:

{gercek}

Kabul etmesi zor ama gerekli.""",
            description="Gerçeklik kontrolü",
            engagement_boost=1.35,
            category="opinion"
        ),
        TweetTemplate(
            name="vulnerable_share",
            template="""Bugün zor bir şey paylaşacağım.

{paylasim}

Bunu neden anlatıyorum?

Çünkü {neden}

Eğer sen de böyle hissediyorsan:

{mesaj}

DM'lerim açık. Yalnız değilsin.""",
            description="Kırılgan paylaşım - derin bağ",
            engagement_boost=1.4,
            category="personal"
        ),
        TweetTemplate(
            name="simple_truth",
            template="""{basit_gercek}

Hepsi bu.

Karmaşıklaştırmayı bırakın.""",
            description="Basit gerçek - minimal ama güçlü",
            engagement_boost=1.25,
            category="opinion"
        ),
    ]

    # Spam kelimeleri (engagement düşürür)
    SPAM_KEYWORDS = [
        "follow for follow", "f4f", "like4like", "dm for collab",
        "buy now", "limited offer", "click link", "free money",
        "giveaway follow", "retweet to win"
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        is_premium: bool = True,
        x_bearer_token: Optional[str] = None
    ):
        """
        Args:
            api_key: Anthropic API key (opsiyonel, env'den de alınabilir)
            is_premium: X Premium kullanıcısı mı (25k karakter)
            x_bearer_token: X API Bearer Token (profil analizi için)
        """
        self.templates = self.TEMPLATES
        self.is_premium = is_premium
        self.max_chars = MAX_CHARS_PREMIUM if is_premium else MAX_CHARS_STANDARD

        # Claude API kurulumu
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = None
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

        # X Profile Analyzer kurulumu
        self.profile_analyzer = XProfileAnalyzer(bearer_token=x_bearer_token)
        self.current_profile: Optional[XProfile] = None

    def calculate_phoenix_score(self, action_predictions: Dict[str, float]) -> Dict[str, any]:
        """
        Phoenix Weighted Scorer - X algoritmasının gerçek puanlama sistemi.

        X'in Rust codebase'inden alınan ağırlıklarla weighted score hesaplar.

        Args:
            action_predictions: Her aksiyon için tahmin edilen olasılıklar
                {"favorite": 0.5, "reply": 0.3, "retweet": 0.2, ...}

        Returns:
            {
                "weighted_score": float,  # Toplam ağırlıklı skor
                "action_contributions": dict,  # Her aksiyonun katkısı
                "positive_sum": float,  # Pozitif sinyaller toplamı
                "negative_sum": float,  # Negatif sinyaller toplamı
                "normalized_score": float,  # 0-100 arası normalize skor
            }
        """
        weighted_sum = 0.0
        positive_sum = 0.0
        negative_sum = 0.0
        contributions = {}

        for action, weight in self.PHOENIX_WEIGHTS.items():
            prediction = action_predictions.get(action, 0.0)
            contribution = prediction * weight
            contributions[action] = contribution

            if weight > 0:
                positive_sum += contribution
            else:
                negative_sum += abs(contribution)

            weighted_sum += contribution

        # Negatif skor offset (X algoritmasından)
        if weighted_sum < 0:
            # Negatif skorları normalize et
            total_negative_weights = sum(abs(w) for w in self.PHOENIX_WEIGHTS.values() if w < 0)
            weighted_sum = (weighted_sum + total_negative_weights) / total_negative_weights * NEGATIVE_SCORES_OFFSET
        else:
            weighted_sum += NEGATIVE_SCORES_OFFSET

        # 0-100 arası normalize et
        max_possible = sum(w for w in self.PHOENIX_WEIGHTS.values() if w > 0)
        normalized = min(100, max(0, (weighted_sum / max_possible) * 100))

        return {
            "weighted_score": round(weighted_sum, 4),
            "action_contributions": contributions,
            "positive_sum": round(positive_sum, 4),
            "negative_sum": round(negative_sum, 4),
            "normalized_score": round(normalized, 1),
        }

    def calculate_author_diversity_penalty(
        self,
        author_position: int,
        decay_factor: float = AUTHOR_DIVERSITY_DECAY,
        floor: float = AUTHOR_DIVERSITY_FLOOR
    ) -> float:
        """
        Author Diversity Scorer - Aynı yazarın tekrarlayan içeriğini cezalandırır.

        X algoritması, aynı yazardan art arda gelen tweetleri cezalandırır.
        İlk tweet: 1.0x, İkinci: 0.5x, Üçüncü: 0.25x, ... minimum: 0.1x

        Args:
            author_position: Yazarın kaçıncı tweet'i (0-indexed)
            decay_factor: Her tekrar için decay oranı (default: 0.5)
            floor: Minimum multiplier (default: 0.1)

        Returns:
            Diversity multiplier (0.1 - 1.0 arası)
        """
        # Formül: (1.0 - floor) * decay^position + floor
        multiplier = (1.0 - floor) * (decay_factor ** author_position) + floor
        return round(multiplier, 3)

    def calculate_oon_adjustment(self, base_score: float, is_in_network: bool) -> float:
        """
        Out-of-Network Adjustment - Takip etmediğin kişilerin içeriğini ayarla.

        X algoritması, takip etmediğin kişilerin içeriklerine %20 penalty uygular.

        Args:
            base_score: Temel skor
            is_in_network: Kullanıcı takip edilenler arasında mı

        Returns:
            Ayarlanmış skor
        """
        if not is_in_network:
            return base_score * OON_WEIGHT_FACTOR
        return base_score

    def analyze_tweet(self, tweet: str) -> TweetAnalysis:
        """
        Tweet'i X algoritmasına göre analiz eder.
        """
        score = 100.0
        strengths = []
        weaknesses = []
        suggestions = []
        engagement_prediction = {}

        char_count = len(tweet)
        words = tweet.split()
        word_count = len(words)

        # TEMEL KALİTE KONTROLLER (önce bunlar)

        # 1. Çok kısa veya anlamsız içerik kontrolü
        if char_count < 10:
            weaknesses.append("Çok kısa - anlamlı içerik yok")
            score = 5.0
            return TweetAnalysis(
                score=round(score, 1),
                strengths=strengths,
                weaknesses=weaknesses,
                suggestions=["En az 2-3 cümlelik anlamlı içerik yazın"],
                engagement_prediction={"favorite": 0.01, "reply": 0.01, "repost": 0.01, "bookmark": 0.01}
            )

        # 2. Kelime sayısı kontrolü
        if word_count < 3:
            weaknesses.append("Çok az kelime - daha fazla bağlam gerekli")
            score *= 0.3

        # 3. Gibberish/rastgele karakter tespiti
        # Türkçe ve İngilizce yaygın harfler
        valid_chars = set('abcçdefgğhıijklmnoöpqrsştuüvwxyzABCÇDEFGĞHIİJKLMNOÖPQRSŞTUÜVWXYZ0123456789 \n.,!?:;\'"-()[]{}@#$%&*+=/<>🧵👇💡✅❌📊🎯💪🔥⚡️📌🔹🔸•')

        # Emoji'leri say ve çıkar
        emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U00002702-\U000027B0]')
        text_without_emoji = emoji_pattern.sub('', tweet)

        # Geçersiz karakter oranı
        invalid_char_count = sum(1 for c in text_without_emoji if c not in valid_chars)
        invalid_ratio = invalid_char_count / max(len(text_without_emoji), 1)

        if invalid_ratio > 0.3:
            weaknesses.append("Çok fazla anlamsız karakter tespit edildi")
            score *= 0.2

        # 4. Tekrarlayan karakter kontrolü (aaaaaaa, !!!!!! gibi)
        repetition_pattern = re.findall(r'(.)\1{4,}', tweet)
        if repetition_pattern:
            weaknesses.append("Aşırı karakter tekrarı - spam gibi görünüyor")
            score *= 0.5

        # 5. Gerçek kelime ve içerik kalitesi kontrolü
        # Yaygın Türkçe ve İngilizce kelimeler
        common_words = {
            # Türkçe
            'bir', 'bu', 've', 'için', 'ile', 'de', 'da', 'ne', 'var', 'yok',
            'ben', 'sen', 'biz', 'siz', 'ama', 'çok', 'daha', 'en', 'gibi',
            'nasıl', 'neden', 'nerede', 'kim', 'hangi', 'kaç', 'şey', 'zaman',
            'öyle', 'böyle', 'şu', 'her', 'hiç', 'artık', 'hala', 'sadece',
            'ise', 'olan', 'olarak', 'sonra', 'önce', 'üzere', 'kadar', 'göre',
            'hakkında', 'arasında', 'dolayı', 'rağmen', 'karşı', 'doğru',
            # İngilizce
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'to', 'of', 'in', 'for',
            'on', 'with', 'at', 'by', 'from', 'or', 'as', 'it', 'that', 'this',
            'but', 'not', 'you', 'all', 'we', 'they', 'her', 'his', 'my', 'your',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'if', 'so',
            'just', 'like', 'think', 'know', 'want', 'need', 'see', 'way',
            'new', 'now', 'look', 'only', 'come', 'its', 'over', 'such', 'even',
            'very', 'after', 'most', 'also', 'made', 'well', 'back', 'through'
        }

        # Keyboard pattern tespiti (anlamsız yazım)
        keyboard_patterns = ['asdf', 'jkl', 'qwer', 'zxcv', 'uiop', 'ghjk',
                            'asd', 'fgh', 'jkl', 'qwe', 'rty', 'dfg', 'cvb', 'bnm']

        tweet_lower_clean = ''.join(c for c in tweet.lower() if c.isalpha())
        keyboard_spam = any(pattern in tweet_lower_clean for pattern in keyboard_patterns)

        if keyboard_spam:
            weaknesses.append("Klavye pattern'i tespit edildi - anlamsız içerik")
            score *= 0.15

        # Gerçek kelime sayımı
        recognized_words = 0
        for word in words:
            clean_word = ''.join(c for c in word.lower() if c.isalpha())
            if clean_word in common_words:
                recognized_words += 1

        # Eğer kelimeler var ama hiçbiri tanınmıyorsa
        if word_count >= 3 and recognized_words == 0:
            # Ek kontrol: en az bir kelime 5+ karakter ve normal görünümlü mü?
            long_normal_words = [w for w in words if len(w) >= 5 and
                                sum(1 for c in w.lower() if c in 'aeıioöuü') >= 1]
            if len(long_normal_words) == 0:
                weaknesses.append("Anlamlı kelime bulunamadı")
                score *= 0.25

        # 6. Sadece büyük/küçük harf veya sayı kontrolü
        alpha_count = sum(1 for c in tweet if c.isalpha())
        if alpha_count < 5:
            weaknesses.append("Yeterli metin içeriği yok")
            score *= 0.3

        # Eğer temel kalite çok düşükse, erken dön
        if score < 20:
            return TweetAnalysis(
                score=round(score, 1),
                strengths=strengths,
                weaknesses=weaknesses,
                suggestions=["Anlamlı, okunabilir bir tweet yazın", "En az 2-3 cümle kullanın"],
                engagement_prediction={"favorite": 0.02, "reply": 0.02, "repost": 0.01, "bookmark": 0.01}
            )

        # UZUNLUK DEĞERLENDİRMESİ (kalite kontrolünden sonra)
        if self.is_premium:
            if char_count < 100:
                weaknesses.append("Tweet kısa - Premium'da daha fazla değer sunabilirsin")
                score *= 0.95
            elif 500 <= char_count <= 2000:
                strengths.append("Optimal uzun form içerik - detaylı ve değerli")
                score *= self.ENGAGEMENT_BOOSTERS["long_form_value"]
            elif char_count > 5000:
                strengths.append("Epik içerik - tam bir makale değerinde")
                score *= 1.15
        else:
            if char_count < 50:
                weaknesses.append("Tweet çok kısa - daha fazla bağlam ekleyin")
                score *= 0.9
            elif char_count > 250:
                suggestions.append("X Premium ile 25,000 karaktere kadar yazabilirsin")

        # Soru kontrolü
        if "?" in tweet:
            strengths.append("Soru içeriyor - reply olasılığı yüksek")
            score *= self.ENGAGEMENT_BOOSTERS["question"]
            engagement_prediction["reply"] = 0.7
        else:
            engagement_prediction["reply"] = 0.3

        # Emoji analizi
        emoji_count = len(re.findall(r'[\U0001F300-\U0001F9FF]', tweet))
        if 1 <= emoji_count <= 5:
            strengths.append("İyi emoji kullanımı")
            score *= self.ENGAGEMENT_BOOSTERS["emoji_moderate"]
        elif emoji_count > 10:
            weaknesses.append("Çok fazla emoji")
            score *= self.ENGAGEMENT_PENALTIES["emoji_overload"]

        # Hashtag analizi
        hashtag_count = len(re.findall(r'#\w+', tweet))
        if hashtag_count > 3:
            weaknesses.append("Çok fazla hashtag - spam gibi görünür")
            score *= self.ENGAGEMENT_PENALTIES["too_many_hashtags"]
        elif 1 <= hashtag_count <= 2:
            strengths.append("İyi hashtag kullanımı")

        # Dış link kontrolü
        if re.search(r'https?://(?!twitter\.com|x\.com)', tweet):
            weaknesses.append("Dış link - algoritma bunu cezalandırır")
            score *= self.ENGAGEMENT_PENALTIES["external_link"]
            suggestions.append("Linki yorumlara taşımayı düşünün")

        # Büyük harf kontrolü
        upper_ratio = sum(1 for c in tweet if c.isupper()) / max(len(tweet.replace(" ", "")), 1)
        if upper_ratio > 0.5:
            weaknesses.append("Çok fazla büyük harf")
            score *= self.ENGAGEMENT_PENALTIES["all_caps"]

        # Spam kelime kontrolü
        tweet_lower = tweet.lower()
        for spam_word in self.SPAM_KEYWORDS:
            if spam_word in tweet_lower:
                weaknesses.append(f"Spam kelimesi: '{spam_word}'")
                score *= self.ENGAGEMENT_PENALTIES["spam_keywords"]
                break

        # Satır arası (okunabilirlik)
        line_count = tweet.count("\n")
        if line_count >= 3:
            strengths.append("İyi formatlanmış - okunabilir")
            score *= self.ENGAGEMENT_BOOSTERS["line_breaks"]

        # Thread hook kontrolü
        if "🧵" in tweet or "thread" in tweet_lower:
            strengths.append("Thread formatı - yüksek engagement")
            score *= self.ENGAGEMENT_BOOSTERS["thread_hook"]

        # Call to action kontrolü
        cta_patterns = ["yorumda", "belirtin", "paylaş", "ne düşünüyorsunuz",
                       "katılıyor musunuz", "hangisi", "kaydet", "bookmark",
                       "dm", "comment", "share", "👇", "⬇️"]
        has_cta = any(cta in tweet_lower for cta in cta_patterns)
        if has_cta:
            strengths.append("Call to action var - etkileşim teşviki")
            score *= self.ENGAGEMENT_BOOSTERS["call_to_action"]
        else:
            suggestions.append("Bir call to action ekle (örn: 'Ne düşünüyorsunuz? 👇')")

        # Skoru 0-100 arasında sınırla
        score = max(0, min(100, score))

        # ============================================================================
        # PHOENIX-STYLE ENGAGEMENT PREDICTION (X Algoritması Ağırlıkları)
        # ============================================================================

        # Base engagement olasılıkları (skor bazlı)
        base_engagement = score / 100

        # Her aksiyon için özel tahminler
        # Soru varsa reply yüksek
        reply_boost = 1.5 if "?" in tweet else 1.0
        # CTA varsa share/bookmark yüksek
        share_boost = 1.3 if has_cta else 1.0
        # Thread ise follow yüksek
        follow_boost = 1.5 if ("🧵" in tweet or "thread" in tweet_lower) else 1.0
        # Görsel referansı varsa photo_expand yüksek
        visual_boost = 1.3 if any(w in tweet_lower for w in ["fotoğraf", "görsel", "image", "pic", "📷", "🖼"]) else 1.0
        # Uzun içerik varsa dwell yüksek
        dwell_boost = 1.4 if char_count > 200 else 1.0

        # Phoenix-style action predictions
        engagement_prediction = {
            # Pozitif aksiyonlar (ağırlıklara göre sıralı)
            "follow_author": min(base_engagement * 0.15 * follow_boost, 0.30),  # En değerli (4.0 ağırlık)
            "share_via_dm": min(base_engagement * 0.20 * share_boost, 0.35),    # 1.5 ağırlık
            "reply": min(base_engagement * 0.35 * reply_boost, 0.70),           # 1.0 ağırlık
            "retweet": min(base_engagement * 0.30, 0.55),                       # 1.0 ağırlık
            "quote": min(base_engagement * 0.25, 0.45),                         # 1.0 ağırlık
            "share": min(base_engagement * 0.30 * share_boost, 0.50),           # 1.0 ağırlık
            "profile_click": min(base_engagement * 0.40, 0.65),                 # 1.0 ağırlık
            "favorite": min(base_engagement * 0.60, 0.85),                      # 0.5 ağırlık (en yaygın)
            "click": min(base_engagement * 0.50, 0.75),                         # 0.5 ağırlık
            "photo_expand": min(base_engagement * 0.35 * visual_boost, 0.55),   # 0.5 ağırlık
            "bookmark": min(base_engagement * 0.25 * share_boost, 0.45),        # Tahmini
            "dwell": min(base_engagement * 0.70 * dwell_boost, 0.90),           # 0.25 ağırlık

            # Negatif aksiyonlar (düşük olmalı)
            "not_interested": max(0.02, (1 - base_engagement) * 0.15),
            "mute_author": max(0.01, (1 - base_engagement) * 0.08),
            "block_author": max(0.005, (1 - base_engagement) * 0.05),
            "report": max(0.001, (1 - base_engagement) * 0.02),
        }

        # Phoenix weighted score hesapla
        phoenix_result = self.calculate_phoenix_score(engagement_prediction)

        return TweetAnalysis(
            score=round(score, 1),
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            engagement_prediction=engagement_prediction,
            profile_boost=phoenix_result["normalized_score"] / 100  # Phoenix score'u profile_boost olarak kullan
        )

    def generate_with_ai(
        self,
        topic: str,
        style: str = "professional",
        tone: str = "engaging",
        length: str = "medium",
        include_cta: bool = True,
        include_emoji: bool = True,
        custom_instructions: str = "",
        language: str = "tr",
        profile: XProfile = None
    ) -> str:
        """
        Claude AI ile yaratıcı tweet üretir.

        Args:
            topic: Tweet konusu
            style: Stil (professional, casual, provocative, storytelling, educational)
            tone: Ton (engaging, controversial, inspirational, humorous, raw)
            length: Uzunluk (short, medium, long, epic)
            include_cta: Call to action eklensin mi
            include_emoji: Emoji kullanılsın mı
            custom_instructions: Özel talimatlar
            language: Dil kodu (tr, en, de, fr, es, ar, zh, ja, ko, pt, ru)
            profile: X profil bilgisi (takipçi, verified, hesap yaşı)

        Returns:
            Üretilen tweet
        """
        if not self.client:
            return "Claude API bağlantısı yok. ANTHROPIC_API_KEY ayarlayın."

        # Dil ayarları
        language_config = {
            "tr": {"name": "Türkçe", "instruction": "Tweet'i Türkçe yaz."},
            "en": {"name": "English", "instruction": "Write the tweet in English."},
            "de": {"name": "Deutsch", "instruction": "Write the tweet in German (Deutsch)."},
            "fr": {"name": "Français", "instruction": "Write the tweet in French (Français)."},
            "es": {"name": "Español", "instruction": "Write the tweet in Spanish (Español)."},
            "ar": {"name": "العربية", "instruction": "Write the tweet in Arabic (العربية)."},
            "zh": {"name": "中文", "instruction": "Write the tweet in Chinese (中文)."},
            "ja": {"name": "日本語", "instruction": "Write the tweet in Japanese (日本語)."},
            "ko": {"name": "한국어", "instruction": "Write the tweet in Korean (한국어)."},
            "pt": {"name": "Português", "instruction": "Write the tweet in Portuguese (Português)."},
            "ru": {"name": "Русский", "instruction": "Write the tweet in Russian (Русский)."},
        }

        lang_info = language_config.get(language, language_config["tr"])
        lang_instruction = lang_info["instruction"]

        # Profil bazlı strateji
        profile_strategy = ""
        if profile:
            followers = profile.followers_count
            is_verified = profile.verified

            if followers < 1000:
                profile_strategy = """
👤 PROFİL: BÜYÜME AŞAMASI (< 1K takipçi)
STRATEJİ:
- Viral potansiyeli YÜKSEK içerik üret (paylaşılabilir, relatable)
- Soru sor, tartışma başlat → Reply ve RT al
- Trending konulara değin → Keşfet'e düş
- Niche topluluklara hitap et → Sadık takipçi kazan
- Hook çok güçlü olmalı → Scroll durdur
- Kişisel hikaye ve deneyim paylaş → Bağ kur
- "Follow için sebep ver" mantığı → Değer sun
"""
            elif followers < 10000:
                profile_strategy = """
👤 PROFİL: GELİŞME AŞAMASI (1K-10K takipçi)
STRATEJİ:
- Tutarlı içerik üret → Marka oluştur
- Thread formatı kullan → Derin değer sun
- Engagement'ı koru → Mevcut kitleyi kaybetme
- Niche'te otorite ol → Spesifik konularda derinleş
- Diğer hesaplarla etkileşim → Networking
- Quote tweet ile görüş bildir → Görünürlük
"""
            elif followers < 100000:
                profile_strategy = """
👤 PROFİL: MİD-TİER (10K-100K takipçi)
STRATEJİ:
- Otoriter ve güvenilir ton kullan
- Değer odaklı içerik → Kaliteyi koru
- Kendi görüşlerini cesurca paylaş
- Trend belirleyici ol, takip etme
- Thread ve uzun içerik → Dwell time
- Tartışmalı konularda pozisyon al
"""
            else:
                profile_strategy = """
👤 PROFİL: BÜYÜK HESAP (100K+ takipçi)
STRATEJİ:
- Otorite ve liderlik tonu
- Orijinal düşünce ve içgörü sun
- Kısa, vurucu mesajlar da işe yarar (zaten görünürlüğün var)
- Topluluk oluştur, kitleyi yönlendir
- Marka değerini koru, tartışmalı konularda dikkatli ol
- Diğer büyük hesaplarla etkileşim
"""

            if is_verified:
                profile_strategy += """
[OK] VERİFİED AVANTAJI:
- TweetCred +100 boost → Daha geniş dağıtım
- Duplicate content'te %30 muafiyet
- Daha cesur ve tartışmalı olabilirsin
- Otorite sinyali güçlü
"""

        length_guide = {
            "short": "100-200 karakter",
            "medium": "300-600 karakter",
            "long": "800-1500 karakter",
            "epic": "2000-4000 karakter (X Premium için)"
        }

        style_guide = {
            "professional": "Profesyonel ve bilgili, otorite sahibi",
            "casual": "Samimi ve rahat, arkadaşça",
            "provocative": "Kışkırtıcı ve düşündürücü, status quo'yu sorgulayan",
            "storytelling": "Hikaye anlatıcı, duygusal bağ kuran",
            "educational": "Öğretici, değer veren, framework sunan"
        }

        tone_guide = {
            "engaging": "Dikkat çekici ve etkileşim odaklı",
            "controversial": "Tartışmalı ve cesur, karşıt görüş",
            "inspirational": "İlham verici ve motive edici",
            "humorous": "Esprili ve eğlenceli",
            "raw": "Ham, dürüst, filtresiz"
        }

        prompt = f"""Sen bir X (Twitter) içerik uzmanısın. X'in açık kaynak algoritmasını (github.com/xai-org/x-algorithm) derinlemesine biliyorsun.

GÖREV: Aşağıdaki kriterlere göre viral potansiyeli yüksek bir tweet yaz.

KONU: {topic}

STİL: {style} - {style_guide.get(style, style)}
TON: {tone} - {tone_guide.get(tone, tone)}
UZUNLUK: {length_guide.get(length, length)}
{profile_strategy}
═══════════════════════════════════════════
X ALGORİTMASI - KRİTİK BİLGİLER
═══════════════════════════════════════════

ENGAGEMENT AĞIRLIKLARI (yüksekten düşüğe):
1. Reply (yanıt) → EN YÜKSEK değer (+1.5x)
2. Repost/Retweet → Yüksek değer (+2.0x)
3. Quote Tweet → Çok yüksek (+2.5x)
4. Bookmark → Kalite sinyali (+0.5x)
5. Like → Temel sinyal (+1.0x)

NEGATİF SİNYALLER (KESİNLİKLE KAÇIN):
- Dış link → Algoritma CEZALANDIRIR (-30% reach)
- 3+ hashtag → Spam gibi görünür (-20%)
- "Follow for follow", "like4like" → Spam tespiti (-50%)
- Tamamı büyük harf → Agresif görünüm (-15%)

POZİTİF SİNYALLER (MUTLAKA KULLAN):
- Satır araları → Okunabilirlik, dwell time artırır (+10%)
- Soru sormak → Reply tetikler (+30%)
- Call to action → Etkileşim teşviki (+20%)
- Thread formatı (🧵) → Yüksek engagement (+35%)
- Kişisel hikaye → Duygusal bağ (+25%)
- Tartışmalı görüş → Engagement patlaması (+40%)

DWELL TIME OPTİMİZASYONU (EN KRİTİK FAKTÖR):
Dwell time = kullanıcının tweet'te geçirdiği süre.
⚠️ 3 SANİYEDEN AZ OKUMA = NEGATİF SİNYAL
Bu negatif sinyal "quality multiplier"ı %15-20 düşürür!

DWELL TIME ARTIRMA TAKTİKLERİ:
- Uzun, değerli içerik → Daha fazla okuma süresi
- Merak uyandıran açılış → "Scroll pass" engellenir
- Liste/madde formatı → Taranabilir, daha uzun kalış
- Hikaye anlatımı → Sonunu merak ettir, okumaya devam
- "Plot twist" veya sürpriz → Dikkat tutar
- Paragraflar arası boşluk → Göz dinlenir, devam eder
- Soru sormak → Düşünme süresi = extra dwell time
- Karşıtlık/Çelişki → "ama", "ancak", "fakat" kullan

GİZLİ BİLGİ - SHADOW HIERARCHY:
- Yeni hesaplar -128 TweetCred skoruyla başlar
- Minimum +17'ye ulaşmadan erişim neredeyse sıfır
- İlk 100 post'ta %0.5'ten düşük like/impression = "engagement debt"
- Engagement debt = postlar sadece %10 dağıtıma girer
- Grok her postu pozitif/negatif diye değerlendiriyor

MENTION STRATEJİSİ (PARA KAZANMA İÇİN KRİTİK):
- İnsanları mention'lara çek
- Mention okuyanlar reklamı görür
- Reklam gelirinin %30-50'si sana gelir
- Tartışma başlat → mention trafiği artar

OPTİMAL TWEET YAPISI:
1. HOOK: İlk cümle dikkat çekici (scroll durdurucu) - DWELL TIME BAŞLAR
2. MERAK: İkinci kısım merak uyandırmalı - OKUMAYA DEVAM
3. DEĞER: Okuyucuya somut fayda sağla - DWELL TIME UZAR
4. FORMAT: Satır araları ile okunabilir - GÖZ YORULMAZ
5. CTA: Sonunda aksiyon çağrısı - MENTION'A ÇEK

{"CALL TO ACTION: Sonunda soru sor veya aksiyon iste (örn: 'Ne düşünüyorsunuz?', 'Kaydet', 'Yorumda paylaş')" if include_cta else "Call to action EKLEME"}
{"EMOJI: Uygun yerlerde 1-3 emoji kullan (abartma, spam görünür)" if include_emoji else "EMOJI KULLANMA"}

{f"EK TALİMATLAR: {custom_instructions}" if custom_instructions else ""}

ÖNEMLİ KURALLAR:
1. Hashtag KULLANMA
2. Link EKLEME
3. "Bu tweet'i beğen" gibi spam ifadeler KULLANMA
4. Özgün ol, şablon gibi görünme
5. İnsanların paylaşmak isteyeceği değer sun

🌍 DİL: {lang_instruction}

Sadece tweet metnini yaz, başka açıklama ekleme."""

        # Uzunluğa göre max_tokens ayarla
        max_tokens_map = {
            "short": 1000,
            "medium": 2000,
            "long": 4000,
            "epic": 8000  # 4000 karakter için ~8000 token gerekebilir
        }
        tokens = max_tokens_map.get(length, 2000)

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            return f"Hata: {str(e)}"

    def generate_thread(
        self,
        topic: str,
        num_tweets: int = 5,
        style: str = "educational",
        language: str = "tr"
    ) -> List[str]:
        """
        Claude AI ile thread üretir.

        Args:
            topic: Thread konusu
            num_tweets: Tweet sayısı
            style: Stil
            language: Dil kodu (tr, en, de, fr, es, ar, zh, ja, ko, pt, ru)

        Returns:
            Tweet listesi
        """
        if not self.client:
            return ["Claude API bağlantısı yok. ANTHROPIC_API_KEY ayarlayın."]

        # Dil ayarları
        language_names = {
            "tr": "Türkçe", "en": "English", "de": "Deutsch", "fr": "Français",
            "es": "Español", "ar": "العربية", "zh": "中文", "ja": "日本語",
            "ko": "한국어", "pt": "Português", "ru": "Русский"
        }
        lang_name = language_names.get(language, "Türkçe")

        prompt = f"""Sen bir X (Twitter) thread uzmanısın.

GÖREV: "{topic}" konusunda {num_tweets} tweet'lik viral bir thread yaz.

THREAD KURALLARI:
1. İlk tweet: Güçlü hook, merak uyandırıcı (🧵 ile başla)
2. Orta tweetler: Her biri değer veren, bağımsız okunabilir
3. Son tweet: Özet + call to action

HER TWEET İÇİN:
- 200-400 karakter arası
- Satır araları kullan
- Emoji kullan ama abartma
- Hashtag KULLANMA
- Link EKLEME

STİL: {style}

🌍 DİL: Thread'i {lang_name} dilinde yaz.

FORMAT: Her tweet'i "---" ile ayır.

Sadece thread'i yaz, açıklama ekleme."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response = message.content[0].text.strip()
            tweets = [t.strip() for t in response.split("---") if t.strip()]
            return tweets
        except Exception as e:
            return [f"Hata: {str(e)}"]

    def rewrite_tweet(self, original: str, style: str = "viral", language: str = "tr") -> str:
        """
        Mevcut tweet'i daha viral hale getirir.

        Args:
            original: Orijinal tweet
            style: Hedef stil (viral, controversial, emotional, educational)
            language: Dil kodu (tr, en, de, fr, es, ar, zh, ja, ko, pt, ru)

        Returns:
            Yeniden yazılmış tweet
        """
        if not self.client:
            return "Claude API bağlantısı yok."

        # Dil ayarları
        language_names = {
            "tr": "Türkçe", "en": "English", "de": "Deutsch", "fr": "Français",
            "es": "Español", "ar": "العربية", "zh": "中文", "ja": "日本語",
            "ko": "한국어", "pt": "Português", "ru": "Русский"
        }
        lang_name = language_names.get(language, "Türkçe")

        prompt = f"""Sen bir X içerik editörüsün.

ORİJİNAL TWEET:
{original}

GÖREV: Bu tweet'i {style} tarzında yeniden yaz.

KURALLAR:
- Ana mesajı koru
- Daha dikkat çekici hale getir
- Satır araları ekle
- Hook güçlendir
- Call to action ekle
- Hashtag ve link EKLEME
- Klişe ifadeler KULLANMA

🌍 DİL: Tweet'i {lang_name} dilinde yaz.

Sadece yeni tweet'i yaz."""

        # Orijinal içerik uzunluğuna göre max_tokens ayarla
        original_len = len(original)
        if original_len > 2000:
            tokens = 8000
        elif original_len > 1000:
            tokens = 4000
        else:
            tokens = 2000

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            return f"Hata: {str(e)}"

    def generate_from_template(self, template_name: str, variables: Dict[str, str]) -> str:
        """Şablondan tweet oluşturur."""
        template = next((t for t in self.templates if t.name == template_name), None)
        if not template:
            raise ValueError(f"Şablon bulunamadı: {template_name}")

        tweet = template.template
        for key, value in variables.items():
            tweet = tweet.replace("{" + key + "}", value)

        return tweet

    def optimize_tweet(self, tweet: str) -> str:
        """Tweet'i algoritma için optimize eder."""
        optimized = tweet

        # Dış linkleri kaldır
        external_links = re.findall(r'https?://(?!twitter\.com|x\.com)\S+', optimized)
        if external_links:
            for link in external_links:
                optimized = optimized.replace(link, "[link yorumda]")

        # Çok fazla hashtag varsa azalt
        hashtags = re.findall(r'#\w+', optimized)
        if len(hashtags) > 2:
            for hashtag in hashtags[2:]:
                optimized = optimized.replace(hashtag, "")

        # CTA yoksa ekle
        if "?" not in optimized and "👇" not in optimized:
            cta_options = [
                "\n\nNe düşünüyorsunuz? 👇",
                "\n\nKatılıyor musunuz?",
                "\n\nDeneyimlerinizi paylaşın 💬",
                "\n\nBu post'u kaydet 🔖"
            ]
            optimized += random.choice(cta_options)

        # Fazla boşlukları temizle
        optimized = re.sub(r'\n{3,}', '\n\n', optimized)
        optimized = re.sub(r' {2,}', ' ', optimized)

        return optimized.strip()

    def suggest_improvements(self, topic: str, style: str = "professional") -> List[str]:
        """Konu için tweet önerileri sunar (AI destekli veya şablon)."""

        # AI varsa AI kullan
        if self.client:
            suggestions = []
            styles = ["professional", "casual", "provocative"]
            for s in styles[:3]:
                tweet = self.generate_with_ai(topic, style=s, length="medium")
                suggestions.append(tweet)
            return suggestions

        # AI yoksa şablon bazlı öneriler
        suggestions = []
        if style == "professional":
            suggestions.append(f"🧵 {topic} hakkında kimsenin anlatmadığı gerçekler:\n\nYıllardır bu alanda çalışıyorum.\n\nBaşlıyoruz 👇")
            suggestions.append(f"{topic} konusunda en sık yapılan 3 hata:\n\n1. [hata1]\n2. [hata2]\n3. [hata3]\n\nKaçıncıyı yapıyorsunuz?")
            suggestions.append(f"Son 5 yılda {topic} ile öğrendiğim en değerli ders:\n\n[ders]\n\nBu tek şey her şeyi değiştirdi.")
        elif style == "casual":
            suggestions.append(f"{topic} hakkında garip bir şey fark ettim 👀\n\n[gözlem]\n\nSadece ben mi böyle düşünüyorum?")
            suggestions.append(f"Dün {topic} ile ilgili bir şey denedim.\n\nSonuç?\n\n[sonuç]\n\nMind = blown 🤯")
        elif style == "provocative":
            suggestions.append(f"Herkes {topic} hakkında yanılıyor.\n\nPopüler görüş: [görüş]\n\nGerçek: [gerçek]\n\nFight me.")
            suggestions.append(f"{topic} endüstrisi sizi kandırıyor.\n\nİşte kimsenin söylemediği gerçek:\n\n[gerçek]")

        return suggestions

    def get_best_posting_times(self) -> Dict[str, List[str]]:
        """En iyi paylaşım zamanlarını döndürür."""
        return {
            "weekdays": ["08:00-09:00", "12:00-13:00", "17:00-18:00", "21:00-22:00"],
            "weekends": ["10:00-11:00", "14:00-15:00", "20:00-21:00"],
            "best_days": ["Salı", "Çarşamba", "Perşembe"],
            "avoid": ["Cuma gece", "Pazar sabah erken"],
            "peak_engagement": ["Salı 10:00", "Çarşamba 12:00", "Perşembe 17:00"]
        }

    def list_templates(self, category: Optional[str] = None) -> List[Dict]:
        """Şablonları listeler."""
        templates = self.templates
        if category:
            templates = [t for t in templates if t.category == category]

        return [
            {
                "name": t.name,
                "description": t.description,
                "template": t.template,
                "engagement_boost": f"+{(t.engagement_boost - 1) * 100:.0f}%",
                "category": t.category
            }
            for t in templates
        ]

    def get_template_categories(self) -> List[str]:
        """Mevcut şablon kategorilerini döndürür."""
        return list(set(t.category for t in self.templates))


def main():
    """CLI arayüzü"""
    import argparse
    import sys

    # Windows UTF-8 encoding fix
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description="X Algorithm-Based Tweet Generator (AI-Powered)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python tweet_generator.py analyze "Tweet metniniz"
  python tweet_generator.py generate "yapay zeka" --style provocative --length long
  python tweet_generator.py thread "startup dersleri" --count 7
  python tweet_generator.py rewrite "eski tweet" --style viral
  python tweet_generator.py templates --category thread
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Komutlar")

    # Analyze
    analyze_parser = subparsers.add_parser("analyze", help="Tweet analizi")
    analyze_parser.add_argument("tweet", help="Tweet metni")

    # Generate (AI)
    gen_parser = subparsers.add_parser("generate", help="AI ile tweet üret")
    gen_parser.add_argument("topic", help="Konu")
    gen_parser.add_argument("--style", default="professional",
                           choices=["professional", "casual", "provocative", "storytelling", "educational"])
    gen_parser.add_argument("--tone", default="engaging",
                           choices=["engaging", "controversial", "inspirational", "humorous", "raw"])
    gen_parser.add_argument("--length", default="medium",
                           choices=["short", "medium", "long", "epic"])

    # Thread (AI)
    thread_parser = subparsers.add_parser("thread", help="AI ile thread üret")
    thread_parser.add_argument("topic", help="Konu")
    thread_parser.add_argument("--count", type=int, default=5, help="Tweet sayısı")
    thread_parser.add_argument("--style", default="educational")

    # Rewrite (AI)
    rewrite_parser = subparsers.add_parser("rewrite", help="Tweet'i yeniden yaz")
    rewrite_parser.add_argument("tweet", help="Orijinal tweet")
    rewrite_parser.add_argument("--style", default="viral",
                               choices=["viral", "controversial", "emotional", "educational"])

    # Templates
    templates_parser = subparsers.add_parser("templates", help="Şablonları listele")
    templates_parser.add_argument("--category", help="Kategori filtresi")

    # Optimize
    opt_parser = subparsers.add_parser("optimize", help="Tweet optimize et")
    opt_parser.add_argument("tweet", help="Tweet metni")

    # Times
    subparsers.add_parser("times", help="En iyi paylaşım zamanları")

    args = parser.parse_args()
    generator = XAlgorithmTweetGenerator()

    if args.command == "analyze":
        analysis = generator.analyze_tweet(args.tweet)
        print("\n" + "="*50)
        print("📊 TWEET ANALİZİ")
        print("="*50)
        print(f"\n🎯 Algoritma Skoru: {analysis.score}/100")
        if analysis.strengths:
            print("\n✅ Güçlü Yönler:")
            for s in analysis.strengths:
                print(f"   • {s}")
        if analysis.weaknesses:
            print("\n❌ Zayıf Yönler:")
            for w in analysis.weaknesses:
                print(f"   • {w}")
        if analysis.suggestions:
            print("\n💡 Öneriler:")
            for s in analysis.suggestions:
                print(f"   • {s}")

    elif args.command == "generate":
        print("\n🤖 AI tweet üretiyor...\n")
        tweet = generator.generate_with_ai(
            args.topic,
            style=args.style,
            tone=args.tone,
            length=args.length
        )
        print("="*50)
        print(tweet)
        print("="*50)
        print(f"\n📏 {len(tweet)} karakter")

    elif args.command == "thread":
        print(f"\n🧵 {args.count} tweet'lik thread üretiliyor...\n")
        tweets = generator.generate_thread(args.topic, args.count, args.style)
        for i, tweet in enumerate(tweets, 1):
            print(f"\n--- Tweet {i}/{len(tweets)} ---")
            print(tweet)

    elif args.command == "rewrite":
        print("\n✨ Tweet yeniden yazılıyor...\n")
        new_tweet = generator.rewrite_tweet(args.tweet, args.style)
        print("ORİJİNAL:")
        print(args.tweet)
        print("\nYENİ VERSİYON:")
        print(new_tweet)

    elif args.command == "templates":
        templates = generator.list_templates(args.category)
        print("\n📝 ŞABLONLAR")
        print("="*50)
        for t in templates:
            print(f"\n🔹 {t['name']} ({t['engagement_boost']}) [{t['category']}]")
            print(f"   {t['description']}")

    elif args.command == "optimize":
        optimized = generator.optimize_tweet(args.tweet)
        print("\n✨ OPTİMİZE EDİLMİŞ:")
        print(optimized)

    elif args.command == "times":
        times = generator.get_best_posting_times()
        print("\n⏰ EN İYİ ZAMANLAR")
        print(f"Hafta içi: {', '.join(times['weekdays'])}")
        print(f"Hafta sonu: {', '.join(times['weekends'])}")
        print(f"En iyi günler: {', '.join(times['best_days'])}")
        print(f"Peak: {', '.join(times['peak_engagement'])}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
