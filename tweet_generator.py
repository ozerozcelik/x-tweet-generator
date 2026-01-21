"""
X Algorithm-Based Tweet Generator
Based on: https://github.com/xai-org/x-algorithm

Bu tool, X'in For You algoritmasının puanlama sistemine göre
tweet'lerinizi optimize etmenize yardımcı olur.
"""

import re
import json
import random
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


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


@dataclass
class TweetAnalysis:
    """Tweet analiz sonucu"""
    score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    engagement_prediction: Dict[str, float]


@dataclass
class TweetTemplate:
    """Tweet şablonu"""
    name: str
    template: str
    description: str
    engagement_boost: float


class XAlgorithmTweetGenerator:
    """
    X Algoritması tabanlı Tweet Generator

    For You feed'inde görünürlüğü artırmak için
    algoritmanın favori ettiği özellikleri kullanır.
    """

    # Engagement artıran faktörler
    ENGAGEMENT_BOOSTERS = {
        "question": 1.3,           # Soru sormak reply'ı artırır
        "call_to_action": 1.2,     # Aksiyon çağrısı
        "controversy": 1.4,        # Tartışmalı konu (dikkatli kullan)
        "storytelling": 1.25,      # Hikaye anlatımı
        "thread_hook": 1.35,       # Thread başlangıcı
        "visual_content": 1.5,     # Görsel içerik
        "timely_topic": 1.3,       # Güncel konu
        "personal_experience": 1.2, # Kişisel deneyim
        "data_insight": 1.15,      # Veri/istatistik
        "emoji_moderate": 1.1,     # Orta düzey emoji (1-3)
        "line_breaks": 1.1,        # Okunabilirlik için satır arası
    }

    # Engagement düşüren faktörler
    ENGAGEMENT_PENALTIES = {
        "external_link": 0.7,      # Dış link (X dışına çıkış)
        "too_many_hashtags": 0.8,  # Çok fazla hashtag (>3)
        "all_caps": 0.85,          # Tamamı büyük harf
        "spam_keywords": 0.5,      # Spam kelimeleri
        "too_long": 0.9,           # Çok uzun tweet
        "no_engagement_hook": 0.8, # Etkileşim çağrısı yok
        "emoji_overload": 0.85,    # Çok fazla emoji (>5)
    }

    # Viral tweet şablonları
    TEMPLATES: List[TweetTemplate] = [
        TweetTemplate(
            name="thread_hook",
            template="🧵 {konu} hakkında bilmeniz gereken {sayi} şey:\n\n(Thread)",
            description="Thread başlangıcı - yüksek engagement",
            engagement_boost=1.35
        ),
        TweetTemplate(
            name="hot_take",
            template="Popüler olmayan görüş:\n\n{gorus}\n\nKatılıyor musunuz?",
            description="Tartışma başlatıcı",
            engagement_boost=1.4
        ),
        TweetTemplate(
            name="story_hook",
            template="Dün {olay} yaşandı.\n\nÖğrendiğim şey:\n\n{ders}",
            description="Hikaye formatı",
            engagement_boost=1.25
        ),
        TweetTemplate(
            name="question_poll",
            template="Soru:\n\n{soru}\n\n🔵 {secenek1}\n🟢 {secenek2}\n\nYorumda belirtin 👇",
            description="Anket tarzı soru",
            engagement_boost=1.3
        ),
        TweetTemplate(
            name="value_list",
            template="{konu} için {sayi} taktik:\n\n1. {madde1}\n2. {madde2}\n3. {madde3}\n\nHangisini deneyeceksiniz?",
            description="Değer listesi",
            engagement_boost=1.2
        ),
        TweetTemplate(
            name="before_after",
            template="Önce: {once}\n\nSonra: {sonra}\n\nFark yaratan tek şey: {fark}",
            description="Dönüşüm hikayesi",
            engagement_boost=1.25
        ),
        TweetTemplate(
            name="myth_buster",
            template="❌ Mit: {mit}\n\n✅ Gerçek: {gercek}\n\nÇoğu insan bunu yanlış biliyor.",
            description="Mit kırıcı",
            engagement_boost=1.3
        ),
        TweetTemplate(
            name="prediction",
            template="2025'te {alan} hakkında tahminim:\n\n{tahmin}\n\nRemindMe 1 year",
            description="Tahmin tweeti",
            engagement_boost=1.2
        ),
        TweetTemplate(
            name="controversial_opinion",
            template="Bunu söylediğim için eleştirileceğim ama:\n\n{gorus}\n\nDeğişiklik mi?",
            description="Cesur görüş",
            engagement_boost=1.35
        ),
        TweetTemplate(
            name="simple_insight",
            template="{basit_sey} yaptım.\n\nSonuç: {sonuc}\n\nBasit ama etkili.",
            description="Basit içgörü",
            engagement_boost=1.15
        ),
    ]

    # Spam kelimeleri (engagement düşürür)
    SPAM_KEYWORDS = [
        "follow for follow", "f4f", "like4like", "dm for collab",
        "buy now", "limited offer", "click link", "free money",
        "giveaway follow", "retweet to win"
    ]

    def __init__(self):
        self.templates = self.TEMPLATES

    def analyze_tweet(self, tweet: str) -> TweetAnalysis:
        """
        Tweet'i X algoritmasına göre analiz eder.

        Args:
            tweet: Analiz edilecek tweet metni

        Returns:
            TweetAnalysis objesi
        """
        score = 100.0
        strengths = []
        weaknesses = []
        suggestions = []
        engagement_prediction = {}

        # Karakter sayısı kontrolü
        char_count = len(tweet)
        if char_count < 50:
            weaknesses.append("Tweet çok kısa - daha fazla bağlam ekleyin")
            score *= 0.9
        elif char_count > 250:
            weaknesses.append("Tweet biraz uzun - özlü tutmaya çalışın")
            score *= self.ENGAGEMENT_PENALTIES["too_long"]
        elif 100 <= char_count <= 200:
            strengths.append("Optimal tweet uzunluğu")
            score *= 1.05

        # Soru kontrolü
        if "?" in tweet:
            strengths.append("Soru içeriyor - reply olasılığı yüksek")
            score *= self.ENGAGEMENT_BOOSTERS["question"]
            engagement_prediction["reply"] = 0.7
        else:
            engagement_prediction["reply"] = 0.3

        # Emoji analizi
        emoji_count = len(re.findall(r'[\U0001F300-\U0001F9FF]', tweet))
        if 1 <= emoji_count <= 3:
            strengths.append("Optimal emoji kullanımı")
            score *= self.ENGAGEMENT_BOOSTERS["emoji_moderate"]
        elif emoji_count > 5:
            weaknesses.append("Çok fazla emoji - profesyonelliği azaltır")
            score *= self.ENGAGEMENT_PENALTIES["emoji_overload"]
        elif emoji_count == 0:
            suggestions.append("1-3 emoji eklemek görünürlüğü artırabilir")

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
            weaknesses.append("Çok fazla büyük harf - bağırmak gibi")
            score *= self.ENGAGEMENT_PENALTIES["all_caps"]

        # Spam kelime kontrolü
        tweet_lower = tweet.lower()
        for spam_word in self.SPAM_KEYWORDS:
            if spam_word in tweet_lower:
                weaknesses.append(f"Spam kelimesi tespit edildi: '{spam_word}'")
                score *= self.ENGAGEMENT_PENALTIES["spam_keywords"]
                break

        # Satır arası kontrolü (okunabilirlik)
        if "\n" in tweet:
            strengths.append("Satır araları var - okunabilirlik iyi")
            score *= self.ENGAGEMENT_BOOSTERS["line_breaks"]
        else:
            suggestions.append("Satır araları eklemek okunabilirliği artırır")

        # Thread hook kontrolü
        if "🧵" in tweet or "thread" in tweet_lower or "(thread)" in tweet_lower:
            strengths.append("Thread formatı - yüksek engagement potansiyeli")
            score *= self.ENGAGEMENT_BOOSTERS["thread_hook"]

        # Call to action kontrolü
        cta_patterns = ["yorumda", "belirtin", "paylaşın", "ne düşünüyorsunuz",
                       "katılıyor musunuz", "hangisi", "comment", "share"]
        has_cta = any(cta in tweet_lower for cta in cta_patterns)
        if has_cta:
            strengths.append("Call to action var - etkileşim teşviki")
            score *= self.ENGAGEMENT_BOOSTERS["call_to_action"]
        else:
            suggestions.append("Bir call to action ekleyin (örn: 'Ne düşünüyorsunuz?')")
            score *= self.ENGAGEMENT_PENALTIES["no_engagement_hook"]

        # Engagement tahminleri
        engagement_prediction["favorite"] = min(score / 150, 0.8)
        engagement_prediction["repost"] = min(score / 200, 0.5)
        engagement_prediction["quote"] = min(score / 250, 0.3)

        return TweetAnalysis(
            score=round(score, 1),
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            engagement_prediction=engagement_prediction
        )

    def generate_from_template(self, template_name: str, variables: Dict[str, str]) -> str:
        """
        Şablondan tweet oluşturur.

        Args:
            template_name: Şablon adı
            variables: Şablon değişkenleri

        Returns:
            Oluşturulan tweet
        """
        template = next((t for t in self.templates if t.name == template_name), None)
        if not template:
            raise ValueError(f"Şablon bulunamadı: {template_name}")

        tweet = template.template
        for key, value in variables.items():
            tweet = tweet.replace("{" + key + "}", value)

        return tweet

    def optimize_tweet(self, tweet: str) -> str:
        """
        Tweet'i algoritma için optimize eder.

        Args:
            tweet: Orijinal tweet

        Returns:
            Optimize edilmiş tweet
        """
        optimized = tweet

        # Dış linkleri kaldır (yoruma taşınmalı)
        external_links = re.findall(r'https?://(?!twitter\.com|x\.com)\S+', optimized)
        if external_links:
            for link in external_links:
                optimized = optimized.replace(link, "[link yorumda]")

        # Çok fazla hashtag varsa azalt
        hashtags = re.findall(r'#\w+', optimized)
        if len(hashtags) > 3:
            for hashtag in hashtags[3:]:
                optimized = optimized.replace(hashtag, "")

        # Soru işareti yoksa ve CTA yoksa ekle
        if "?" not in optimized:
            cta_options = [
                "\n\nNe düşünüyorsunuz?",
                "\n\nKatılıyor musunuz?",
                "\n\nDeneyimlerinizi paylaşın 👇"
            ]
            optimized += random.choice(cta_options)

        # Fazla boşlukları temizle
        optimized = re.sub(r'\n{3,}', '\n\n', optimized)
        optimized = re.sub(r' {2,}', ' ', optimized)

        return optimized.strip()

    def suggest_improvements(self, topic: str, style: str = "professional") -> List[str]:
        """
        Konu için tweet önerileri sunar.

        Args:
            topic: Tweet konusu
            style: Stil (professional, casual, provocative)

        Returns:
            Tweet önerileri listesi
        """
        suggestions = []

        # Farklı şablonları konuya uygula
        if style == "professional":
            suggestions.append(f"🧵 {topic} hakkında bilmeniz gereken 5 şey:\n\n(Thread)")
            suggestions.append(f"{topic} konusunda en sık yapılan hata:\n\n[hatayı ekleyin]\n\nÇözüm basit ama çoğu kişi bilmiyor.")
            suggestions.append(f"3 yıldır {topic} ile çalışıyorum.\n\nÖğrendiğim en değerli ders:\n\n[dersi ekleyin]")

        elif style == "casual":
            suggestions.append(f"{topic} hakkında kimsenin konuşmadığı bir şey var 👀\n\n[içeriği ekleyin]")
            suggestions.append(f"Bugün {topic} ile ilgili bir keşif yaptım:\n\n[keşfi ekleyin]\n\nGame changer olabilir")

        elif style == "provocative":
            suggestions.append(f"Popüler olmayan görüş:\n\n{topic} hakkında çoğu kişi yanılıyor.\n\nİşte neden:")
            suggestions.append(f"Bunu söylediğim için eleştirileceğim ama:\n\n{topic} [cesur görüşünüz]\n\nFight me.")

        return suggestions

    def get_best_posting_times(self) -> Dict[str, List[str]]:
        """
        En iyi paylaşım zamanlarını döndürür (genel veriler).

        Returns:
            Gün bazında optimal saatler
        """
        return {
            "weekdays": ["08:00-09:00", "12:00-13:00", "17:00-18:00", "21:00-22:00"],
            "weekends": ["10:00-11:00", "14:00-15:00", "20:00-21:00"],
            "best_days": ["Salı", "Çarşamba", "Perşembe"],
            "avoid": ["Cuma gece", "Pazar sabah erken"]
        }

    def list_templates(self) -> List[Dict]:
        """Tüm şablonları listeler."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "template": t.template,
                "engagement_boost": f"{(t.engagement_boost - 1) * 100:.0f}%"
            }
            for t in self.templates
        ]


def main():
    """CLI arayüzü"""
    import argparse
    import sys

    # Windows UTF-8 encoding fix
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description="X Algorithm-Based Tweet Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python tweet_generator.py analyze "Tweet metniniz burada"
  python tweet_generator.py templates
  python tweet_generator.py generate thread_hook --vars '{"konu": "AI", "sayi": "5"}'
  python tweet_generator.py optimize "Tweet metniniz"
  python tweet_generator.py suggest "yapay zeka" --style professional
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Komutlar")

    # Analyze komutu
    analyze_parser = subparsers.add_parser("analyze", help="Tweet'i analiz et")
    analyze_parser.add_argument("tweet", help="Analiz edilecek tweet")

    # Templates komutu
    subparsers.add_parser("templates", help="Şablonları listele")

    # Generate komutu
    generate_parser = subparsers.add_parser("generate", help="Şablondan tweet oluştur")
    generate_parser.add_argument("template", help="Şablon adı")
    generate_parser.add_argument("--vars", help="JSON formatında değişkenler", required=True)

    # Optimize komutu
    optimize_parser = subparsers.add_parser("optimize", help="Tweet'i optimize et")
    optimize_parser.add_argument("tweet", help="Optimize edilecek tweet")

    # Suggest komutu
    suggest_parser = subparsers.add_parser("suggest", help="Konu için öneriler")
    suggest_parser.add_argument("topic", help="Tweet konusu")
    suggest_parser.add_argument("--style", choices=["professional", "casual", "provocative"],
                               default="professional", help="Tweet stili")

    # Times komutu
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

        print("\n📈 Engagement Tahmini:")
        for action, prob in analysis.engagement_prediction.items():
            bar = "█" * int(prob * 20) + "░" * (20 - int(prob * 20))
            print(f"   {action:10} [{bar}] {prob*100:.0f}%")

    elif args.command == "templates":
        templates = generator.list_templates()
        print("\n" + "="*50)
        print("📝 TWEET ŞABLONLARI")
        print("="*50)
        for t in templates:
            print(f"\n🔹 {t['name']} (+{t['engagement_boost']} engagement)")
            print(f"   {t['description']}")
            print(f"   Şablon: {t['template'][:60]}...")

    elif args.command == "generate":
        variables = json.loads(args.vars)
        tweet = generator.generate_from_template(args.template, variables)
        print("\n" + "="*50)
        print("🐦 OLUŞTURULAN TWEET")
        print("="*50)
        print(f"\n{tweet}")
        print(f"\n📏 Karakter: {len(tweet)}/280")

    elif args.command == "optimize":
        optimized = generator.optimize_tweet(args.tweet)
        print("\n" + "="*50)
        print("✨ OPTİMİZE EDİLMİŞ TWEET")
        print("="*50)
        print(f"\nOrijinal:\n{args.tweet}")
        print(f"\nOptimize:\n{optimized}")
        print(f"\n📏 Karakter: {len(optimized)}/280")

    elif args.command == "suggest":
        suggestions = generator.suggest_improvements(args.topic, args.style)
        print("\n" + "="*50)
        print(f"💡 '{args.topic}' İÇİN ÖNERİLER ({args.style})")
        print("="*50)
        for i, s in enumerate(suggestions, 1):
            print(f"\n{i}. {s}")

    elif args.command == "times":
        times = generator.get_best_posting_times()
        print("\n" + "="*50)
        print("⏰ EN İYİ PAYLAŞIM ZAMANLARI")
        print("="*50)
        print(f"\n📅 Hafta içi: {', '.join(times['weekdays'])}")
        print(f"📅 Hafta sonu: {', '.join(times['weekends'])}")
        print(f"🌟 En iyi günler: {', '.join(times['best_days'])}")
        print(f"⚠️ Kaçının: {', '.join(times['avoid'])}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
