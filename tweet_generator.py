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
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

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


# X Algoritması Ağırlıkları (tahminî değerler - gerçek değerler gizli)
ACTION_WEIGHTS = {
    ActionType.FAVORITE: 1.0,
    ActionType.REPLY: 1.5,
    ActionType.REPOST: 2.0,
    ActionType.QUOTE: 2.5,
    ActionType.CLICK: 0.3,
    ActionType.PROFILE_CLICK: 0.5,
    ActionType.VIDEO_VIEW: 0.8,
    ActionType.PHOTO_EXPAND: 0.4,
    ActionType.SHARE: 1.8,
    ActionType.DWELL: 0.6,
    ActionType.FOLLOW_AUTHOR: 3.0,
    ActionType.NOT_INTERESTED: -2.0,
    ActionType.BLOCK_AUTHOR: -5.0,
    ActionType.MUTE_AUTHOR: -3.0,
    ActionType.REPORT: -10.0,
}

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
            analysis["strengths"].append("Doğrulanmış hesap ✓")
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

    def calculate_reach_prediction(self, profile: XProfile, tweet_score: float) -> Dict[str, int]:
        """
        Profil ve tweet skoruna göre tahmini reach hesaplar.

        Args:
            profile: XProfile objesi
            tweet_score: Tweet analiz skoru (0-100)

        Returns:
            Tahmini reach metrikleri
        """
        base_reach = profile.followers_count

        # Tweet skoru çarpanı
        score_multiplier = tweet_score / 100

        # Tier çarpanı (engagement rate)
        tier_mult = self.TIER_MULTIPLIERS[profile.engagement_tier]

        # Tahmini metrikler
        impressions = int(base_reach * score_multiplier * 2)  # Takipçilerin 2x'i kadar
        engagements = int(impressions * tier_mult * 0.05)  # %5 base engagement
        likes = int(engagements * 0.6)
        retweets = int(engagements * 0.15)
        replies = int(engagements * 0.1)
        bookmarks = int(engagements * 0.1)
        profile_visits = int(engagements * 0.05)

        return {
            "impressions": impressions,
            "engagements": engagements,
            "likes": likes,
            "retweets": retweets,
            "replies": replies,
            "bookmarks": bookmarks,
            "profile_visits": profile_visits,
            "engagement_rate": round((engagements / max(impressions, 1)) * 100, 2)
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

    # Engagement artıran faktörler
    ENGAGEMENT_BOOSTERS = {
        "question": 1.3,
        "call_to_action": 1.2,
        "controversy": 1.4,
        "storytelling": 1.25,
        "thread_hook": 1.35,
        "visual_content": 1.5,
        "timely_topic": 1.3,
        "personal_experience": 1.2,
        "data_insight": 1.15,
        "emoji_moderate": 1.1,
        "line_breaks": 1.1,
        "long_form_value": 1.2,  # Premium için uzun içerik
    }

    # Engagement düşüren faktörler
    ENGAGEMENT_PENALTIES = {
        "external_link": 0.7,
        "too_many_hashtags": 0.8,
        "all_caps": 0.85,
        "spam_keywords": 0.5,
        "no_engagement_hook": 0.8,
        "emoji_overload": 0.85,
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

        # Engagement tahminleri
        engagement_prediction["favorite"] = min(score / 150, 0.85)
        engagement_prediction["repost"] = min(score / 200, 0.6)
        engagement_prediction["quote"] = min(score / 250, 0.4)
        engagement_prediction["bookmark"] = min(score / 180, 0.5)

        return TweetAnalysis(
            score=round(score, 1),
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            engagement_prediction=engagement_prediction
        )

    def generate_with_ai(
        self,
        topic: str,
        style: str = "professional",
        tone: str = "engaging",
        length: str = "medium",
        include_cta: bool = True,
        include_emoji: bool = True,
        custom_instructions: str = ""
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

        Returns:
            Üretilen tweet
        """
        if not self.client:
            return "Claude API bağlantısı yok. ANTHROPIC_API_KEY ayarlayın."

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

Sadece tweet metnini yaz, başka açıklama ekleme."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
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
        style: str = "educational"
    ) -> List[str]:
        """
        Claude AI ile thread üretir.

        Args:
            topic: Thread konusu
            num_tweets: Tweet sayısı
            style: Stil

        Returns:
            Tweet listesi
        """
        if not self.client:
            return ["Claude API bağlantısı yok. ANTHROPIC_API_KEY ayarlayın."]

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

    def rewrite_tweet(self, original: str, style: str = "viral") -> str:
        """
        Mevcut tweet'i daha viral hale getirir.

        Args:
            original: Orijinal tweet
            style: Hedef stil (viral, controversial, emotional, educational)

        Returns:
            Yeniden yazılmış tweet
        """
        if not self.client:
            return "Claude API bağlantısı yok."

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

Sadece yeni tweet'i yaz."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
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
