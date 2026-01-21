"""
X Algorithm Tweet Generator - Web Interface
AI-Powered with Claude API + Profile Analysis
"""

import streamlit as st
import os
from tweet_generator import XAlgorithmTweetGenerator, XProfileAnalyzer, TweetCredAnalyzer

# Sayfa ayarları
st.set_page_config(
    page_title="X Tweet Generator",
    page_icon="🐦",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1DA1F2, #14171A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .score-box {
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
    }
    .score-high { background-color: #d4edda; color: #155724; }
    .score-medium { background-color: #fff3cd; color: #856404; }
    .score-low { background-color: #f8d7da; color: #721c24; }
    .ai-badge {
        background: linear-gradient(90deg, #8B5CF6, #D946EF);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
    }
    .profile-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "anthropic_api_key" not in st.session_state:
    st.session_state.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if "profile_followers" not in st.session_state:
    st.session_state.profile_followers = 1000
if "profile_verified" not in st.session_state:
    st.session_state.profile_verified = False
if "total_posts" not in st.session_state:
    st.session_state.total_posts = 0
if "avg_like_rate" not in st.session_state:
    st.session_state.avg_like_rate = 0.01
if "country" not in st.session_state:
    st.session_state.country = "TR"
if "niche" not in st.session_state:
    st.session_state.niche = "genel"

# Sidebar - Ayarlar
with st.sidebar:
    st.header("⚙️ Ayarlar")

    st.subheader("🤖 AI Ayarları")
    anthropic_key = st.text_input(
        "Anthropic API Key",
        value=st.session_state.anthropic_api_key,
        type="password",
        help="Claude AI için gerekli",
        key="api_key_input"
    )

    # API key değişti mi kontrol et
    if anthropic_key != st.session_state.anthropic_api_key:
        st.session_state.anthropic_api_key = anthropic_key
        st.rerun()

    is_premium = st.checkbox("X Premium Hesabı", value=True, help="25,000 karakter limiti")

    st.markdown("---")

    st.subheader("👤 Profil Bilgileri")
    st.caption("Reach tahmini için profil bilgilerinizi girin")

    followers = st.number_input(
        "Takipçi Sayısı",
        min_value=0,
        max_value=100000000,
        value=st.session_state.profile_followers,
        step=100,
        key="followers_input"
    )
    st.session_state.profile_followers = followers

    following = st.number_input(
        "Takip Sayısı",
        min_value=0,
        max_value=100000000,
        value=500,
        step=100
    )

    verified = st.checkbox("Doğrulanmış Hesap ✓", value=st.session_state.profile_verified)
    st.session_state.profile_verified = verified

    account_age = st.slider("Hesap Yaşı (yıl)", 0.0, 15.0, 2.0, 0.5)

    st.markdown("---")

    st.subheader("📊 TweetCred Bilgileri")
    st.caption("Algoritma analizi için")

    total_posts = st.number_input(
        "Toplam Tweet Sayısı",
        min_value=0,
        max_value=1000000,
        value=st.session_state.total_posts,
        step=10
    )
    st.session_state.total_posts = total_posts

    avg_like_rate = st.slider(
        "Ort. Beğeni Oranı (%)",
        min_value=0.0,
        max_value=10.0,
        value=st.session_state.avg_like_rate * 100,
        step=0.1,
        help="Beğeni / Görüntülenme oranı"
    ) / 100
    st.session_state.avg_like_rate = avg_like_rate

    country = st.selectbox(
        "Ülke",
        ["TR", "US", "EU", "OTHER"],
        format_func=lambda x: {
            "TR": "🇹🇷 Türkiye (Tier 3)",
            "US": "🇺🇸 ABD (Tier 1)",
            "EU": "🇪🇺 Avrupa (Tier 2)",
            "OTHER": "🌍 Diğer"
        }[x],
        index=["TR", "US", "EU", "OTHER"].index(st.session_state.country)
    )
    st.session_state.country = country

    niche = st.selectbox(
        "Niş/Sektör",
        ["genel", "finans", "kripto", "teknoloji", "eglence", "spor", "saglik", "egitim"],
        format_func=lambda x: {
            "genel": "📌 Genel",
            "finans": "💰 Finans/Banka",
            "kripto": "₿ Kripto/Trading",
            "teknoloji": "💻 Teknoloji",
            "eglence": "🎬 Eğlence",
            "spor": "⚽ Spor",
            "saglik": "🏥 Sağlık",
            "egitim": "📚 Eğitim"
        }[x]
    )
    st.session_state.niche = niche

    st.markdown("---")

    # Durum göstergeleri
    if st.session_state.anthropic_api_key:
        st.success("✅ AI Aktif")
    else:
        st.warning("⚠️ AI için API key girin")

    # Profil tier'ı göster
    if followers >= 1000000:
        tier = "🌟 Mega (1M+)"
    elif followers >= 100000:
        tier = "⭐ Macro (100K+)"
    elif followers >= 10000:
        tier = "🔥 Mid (10K+)"
    elif followers >= 1000:
        tier = "💪 Micro (1K+)"
    elif followers >= 100:
        tier = "🌱 Nano (100+)"
    else:
        tier = "🆕 Starter"
    st.info(f"Profil Tier: {tier}")

    # TweetCred durumu
    if verified:
        st.success("🎯 TweetCred: +100 (Verified)")
    elif account_age >= 2 and followers >= 1000:
        st.success("🎯 TweetCred: Pozitif")
    elif account_age < 1 or followers < 100:
        st.warning("🎯 TweetCred: Düşük Risk")

    # Engagement Debt uyarısı
    if total_posts > 0 and total_posts < 100 and avg_like_rate < 0.005:
        st.error("⚠️ Engagement Debt Riski!")

# Generator oluştur
generator = XAlgorithmTweetGenerator(
    api_key=st.session_state.anthropic_api_key if st.session_state.anthropic_api_key else None,
    is_premium=is_premium
)

# Profile analyzer
profile_analyzer = XProfileAnalyzer()
manual_profile = profile_analyzer.create_manual_profile(
    username="user",
    followers=followers,
    following=following,
    verified=verified,
    account_age_years=account_age
)

# TweetCred analyzer
tweetcred_analyzer = TweetCredAnalyzer()

# Header
st.markdown('<p class="main-header">🐦 X Algorithm Tweet Generator</p>', unsafe_allow_html=True)

# AI durumu
col_status1, col_status2 = st.columns(2)
with col_status1:
    if generator.client:
        st.markdown('<span class="ai-badge">🤖 AI Powered</span>', unsafe_allow_html=True)
with col_status2:
    st.markdown(f'<span class="ai-badge">👤 {followers:,} takipçi</span>', unsafe_allow_html=True)

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🤖 AI Tweet Üret",
    "📊 Tweet Analizi",
    "🎯 TweetCred",
    "💰 Monetization",
    "🧵 Thread Oluştur",
    "✨ Yeniden Yaz",
    "📝 Şablonlar",
    "⏰ Zamanlar"
])

# Tab 1: AI Tweet Üretimi
with tab1:
    st.header("🤖 AI ile Tweet Üret")

    if not generator.client:
        st.info("👈 Sol menüden **Anthropic API Key** girerek AI özelliklerini aktifleştirin.")
        st.markdown("""
        **API Key nasıl alınır:**
        1. [console.anthropic.com](https://console.anthropic.com) adresine gidin
        2. Hesap oluşturun veya giriş yapın
        3. API Keys bölümünden yeni key oluşturun
        4. Key'i sol menüdeki alana yapıştırın
        """)
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            topic = st.text_input(
                "Konu:",
                placeholder="örn: yapay zeka, startup, kariyer...",
                key="ai_topic"
            )

        with col2:
            length = st.selectbox(
                "Uzunluk:",
                ["short", "medium", "long", "epic"],
                format_func=lambda x: {
                    "short": "📝 Kısa (100-200)",
                    "medium": "📄 Orta (300-600)",
                    "long": "📰 Uzun (800-1500)",
                    "epic": "📚 Epik (2000-4000)"
                }[x],
                index=1,
                key="ai_length"
            )

        col3, col4 = st.columns(2)
        with col3:
            style = st.selectbox(
                "Stil:",
                ["professional", "casual", "provocative", "storytelling", "educational"],
                format_func=lambda x: {
                    "professional": "🎩 Profesyonel",
                    "casual": "😎 Casual",
                    "provocative": "🔥 Provokatif",
                    "storytelling": "📖 Hikaye",
                    "educational": "🎓 Eğitici"
                }[x],
                key="ai_style"
            )
        with col4:
            tone = st.selectbox(
                "Ton:",
                ["engaging", "controversial", "inspirational", "humorous", "raw"],
                format_func=lambda x: {
                    "engaging": "💬 Etkileşimci",
                    "controversial": "⚡ Tartışmalı",
                    "inspirational": "✨ İlham Verici",
                    "humorous": "😄 Esprili",
                    "raw": "💯 Ham/Dürüst"
                }[x],
                key="ai_tone"
            )

        col5, col6 = st.columns(2)
        with col5:
            include_cta = st.checkbox("Call to Action ekle", value=True, key="ai_cta")
        with col6:
            include_emoji = st.checkbox("Emoji kullan", value=True, key="ai_emoji")

        custom_instructions = st.text_area(
            "Özel talimatlar (opsiyonel):",
            height=80,
            placeholder="örn: Benim sektörüm fintech, hedef kitle yatırımcılar...",
            key="ai_custom"
        )

        if st.button("🚀 Tweet Üret", type="primary", use_container_width=True, key="ai_generate"):
            if topic:
                with st.spinner("🤖 AI tweet üretiyor..."):
                    tweet = generator.generate_with_ai(
                        topic=topic,
                        style=style,
                        tone=tone,
                        length=length,
                        include_cta=include_cta,
                        include_emoji=include_emoji,
                        custom_instructions=custom_instructions
                    )

                st.success("Tweet üretildi!")
                st.text_area("Üretilen Tweet:", value=tweet, height=250, key="ai_result")
                st.caption(f"📏 {len(tweet)} karakter")

                # Analiz ve reach tahmini
                col_a, col_b = st.columns(2)
                with col_a:
                    analysis = generator.analyze_tweet(tweet)
                    st.metric("Algoritma Skoru", f"{analysis.score}/100")

                with col_b:
                    reach = profile_analyzer.calculate_reach_prediction(manual_profile, analysis.score)
                    st.metric("Tahmini Görüntülenme", f"{reach['impressions']:,}")
            else:
                st.warning("Lütfen bir konu girin.")

# Tab 2: Tweet Analizi
with tab2:
    st.header("📊 Tweet Analizi")

    tweet_input = st.text_area(
        "Tweet'inizi yazın:",
        height=200,
        placeholder="Analiz edilecek tweet...",
        key="analyze_tweet_input"
    )

    char_count = len(tweet_input)
    max_chars = 25000 if is_premium else 280
    st.caption(f"📏 {char_count:,}/{max_chars:,} karakter")

    if st.button("🔍 Analiz Et", type="primary", use_container_width=True, key="analyze_btn"):
        if tweet_input.strip():
            analysis = generator.analyze_tweet(tweet_input)

            col1, col2 = st.columns([1, 2])

            with col1:
                score = analysis.score
                if score >= 80:
                    score_class = "score-high"
                    emoji = "🚀"
                elif score >= 50:
                    score_class = "score-medium"
                    emoji = "👍"
                else:
                    score_class = "score-low"
                    emoji = "⚠️"

                st.markdown(f"""
                <div class="score-box {score_class}">
                    {emoji} {score}/100
                </div>
                """, unsafe_allow_html=True)

                st.markdown("---")

                # Reach tahmini
                reach = profile_analyzer.calculate_reach_prediction(manual_profile, score)
                st.subheader("📈 Tahmini Reach")
                st.metric("Görüntülenme", f"{reach['impressions']:,}")
                st.metric("Beğeni", f"{reach['likes']:,}")
                st.metric("Retweet", f"{reach['retweets']:,}")
                st.metric("Yorum", f"{reach['replies']:,}")

            with col2:
                if analysis.strengths:
                    st.subheader("✅ Güçlü Yönler")
                    for s in analysis.strengths:
                        st.success(s)

                if analysis.weaknesses:
                    st.subheader("❌ Zayıf Yönler")
                    for w in analysis.weaknesses:
                        st.error(w)

                if analysis.suggestions:
                    st.subheader("💡 Öneriler")
                    for s in analysis.suggestions:
                        st.info(s)

                # Profil bazlı öneriler
                profile_analysis = profile_analyzer.analyze_profile(manual_profile)
                if profile_analysis["suggestions"]:
                    st.subheader("👤 Profil Önerileri")
                    for s in profile_analysis["suggestions"]:
                        st.warning(s)
        else:
            st.warning("Lütfen bir tweet yazın.")

# Tab 3: TweetCred Analizi
with tab3:
    st.header("🎯 TweetCred Skoru & Shadow Hierarchy")

    st.markdown("""
    <div class="profile-card">
        <h4>TweetCred Nedir?</h4>
        <p>Jack Dorsey'in geliştirdiği gizli otorite ölçeği. Hesabınızın algoritmadaki "güvenilirlik puanı"dır.</p>
        <ul>
            <li>Yeni hesaplar <strong>-128</strong> ile başlar</li>
            <li>Minimum <strong>+17</strong> olmalı reach almak için</li>
            <li>Verified hesaplar <strong>+100</strong> bonus alır</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # TweetCred hesaplama
    tweetcred = tweetcred_analyzer.calculate_tweetcred(
        profile=manual_profile,
        avg_engagement_rate=avg_like_rate
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        # TweetCred skoru
        score = tweetcred.total_score
        if tweetcred.is_positive:
            score_color = "score-high"
            status_emoji = "✅"
            status_text = "REACH ALIYORSUNUZ"
        elif score >= 0:
            score_color = "score-medium"
            status_emoji = "⚠️"
            status_text = "SINIRDA"
        else:
            score_color = "score-low"
            status_emoji = "❌"
            status_text = "REACH KISITLI"

        st.markdown(f"""
        <div class="score-box {score_color}">
            {status_emoji} TweetCred<br>
            {score:+d}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**Durum:** {status_text}")
        if tweetcred.has_cold_start_suppression:
            st.error("⚠️ Cold Start Suppression Aktif!")
        st.metric("Dağıtım Yüzdesi", f"{tweetcred.distribution_rate:.0%}")

    with col2:
        # Faktör breakdown
        st.subheader("📊 Skor Bileşenleri")

        factors = {
            "Base Score": tweetcred.base_score,
            "Verified Bonus": tweetcred.verified_boost,
            "Bio Score": tweetcred.bio_score,
            "Follower Ratio": tweetcred.ratio_score,
            "Language Score": tweetcred.language_score,
            "Engagement History": tweetcred.engagement_history_score,
            "Niche Focus": tweetcred.niche_focus_score
        }

        for label, value in factors.items():
            if value > 0:
                st.success(f"✓ {label}: +{value}")
            elif value < 0:
                st.error(f"✗ {label}: {value}")
            else:
                st.info(f"○ {label}: {value}")

        # Öneriler
        st.subheader("💡 TweetCred İyileştirme")
        tips = []
        if not verified:
            tips.append("Verified olmak +100 boost sağlar")
        if followers < 1000:
            tips.append("Takipçi sayısını artırın (1K+ hedef)")
        if avg_like_rate < 0.02:
            tips.append("Etkileşim oranınızı %2+ yapın")

        for tip in tips:
            st.warning(tip)

    st.markdown("---")

    # Engagement Debt Analizi
    st.subheader("⚠️ Engagement Debt (Cold Start Suppression)")

    # Yaklaşık değerler hesapla
    est_impressions = max(followers * 10, 1000) if total_posts > 0 else 1000
    est_likes = int(est_impressions * avg_like_rate)

    engagement_debt = tweetcred_analyzer.analyze_engagement_debt(
        posts=total_posts,
        likes=est_likes,
        impressions=est_impressions
    )

    col3, col4 = st.columns(2)

    with col3:
        if engagement_debt.has_debt:
            st.error(f"""
            **ENGAGEMENT DEBT AKTİF**

            Beğeni oranınız: {engagement_debt.engagement_rate:.2%}
            Bu %0.5 eşiğinin altında!

            **Şiddet:** {engagement_debt.severity.upper()}
            **Borç Seviyesi:** {engagement_debt.debt_level:.0%}
            """)
        else:
            if total_posts < 100:
                st.warning(f"""
                **KRİTİK DÖNEM**

                İlk 100 postta {100 - total_posts} post kaldı.
                Şu anki oran: {engagement_debt.engagement_rate:.2%}

                **Dikkat:** %0.5'in üstünde kalın!
                """)
            else:
                st.success(f"""
                **ENGAGEMENT DEBT YOK**

                Beğeni oranınız: {engagement_debt.engagement_rate:.2%}
                Dağıtım: %100
                """)

    with col4:
        st.subheader("🔧 Çıkış Stratejileri")
        strategies = [
            "Viral potansiyelli kaliteli içerik paylaşın",
            "Niche topluluklarla etkileşime girin",
            "En aktif saatlerde paylaşım yapın",
            "Soru soran veya tartışma başlatan tweetler atın",
            "İlk 100 tweet'te agresif promosyon yapmayın"
        ]
        for strategy in strategies:
            st.info(strategy)

    st.markdown("---")

    # Dwell Time ipuçları
    st.subheader("⏱️ Dwell Time Optimizasyonu")
    st.markdown("""
    **Kritik Bilgi:** 3 saniyeden az okuma = NEGATİF SİNYAL

    Algoritmaya göre tweet'inizin okunma süresi düşükse, kalite çarpanınız %15-20 düşer.
    """)

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("**Dwell Time Artırma Teknikleri:**")
        increase_tips = [
            "Uzun, katmanlı içerik yazın (150+ kelime)",
            "Satır araları kullanın (okuma hızını düşürür)",
            "Listeler ve bullet point'ler ekleyin",
            "İlk cümleyi merak uyandırıcı yapın",
            "Son satırı call-to-action yapın",
            "Hikaye formatı kullanın"
        ]
        for tip in increase_tips:
            st.success(f"✓ {tip}")

    with col6:
        st.markdown("**Kaçınılması Gerekenler:**")
        avoid_tips = [
            "Tek satırlık tweetler",
            "Sadece link paylaşmak",
            "Anlaşılması zor jargon",
            "Çok uzun paragraflar (göz yorar)",
            "Emoji spam (dikkat dağıtır)"
        ]
        for avoid in avoid_tips:
            st.error(f"✗ {avoid}")

# Tab 4: Monetization
with tab4:
    st.header("💰 Monetization Analizi")

    st.markdown("""
    <div class="profile-card">
        <h4>X Monetization Nasıl Çalışır?</h4>
        <p>Sabit ödeme YOK! Reklam gelirinin <strong>%30-50</strong>'sini alırsınız.</p>
        <p><strong>RPM (1000 görüntülenme başı gelir)</strong> ülkeye ve nişe göre değişir:</p>
        <ul>
            <li>🇺🇸 ABD: $2-8 RPM</li>
            <li>🇪🇺 Avrupa: $1-4 RPM</li>
            <li>🇹🇷 Türkiye (Tier 3): $0.05-0.5 RPM</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Monetization analizi
    monetization = tweetcred_analyzer.get_monetization_analysis(
        profile=manual_profile,
        niche=niche,
        target_market=country
    )

    # Ülke tier'ına göre RPM hesapla
    tier_map = {"US": "Tier 1", "EU": "Tier 2", "TR": "Tier 3", "OTHER": "Tier 3"}
    country_tier = tier_map.get(country, "Tier 3")

    # Tahmini aylık potansiyel (günde 3 tweet, 10% reach varsayımı)
    daily_impressions = followers * 0.1 * 3 if followers > 0 else 300
    monthly_impressions = daily_impressions * 30
    monthly_potential = (monthly_impressions / 1000) * monetization.estimated_rpm

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Tahmini RPM",
            f"${monetization.estimated_rpm:.2f}",
            help="1000 görüntülenme başı gelir"
        )

    with col2:
        st.metric(
            "Aylık Potansiyel",
            f"${monthly_potential:.2f}",
            help="Günde 3 tweet varsayımıyla"
        )

    with col3:
        tier_colors = {"Tier 1": "🟢", "Tier 2": "🟡", "Tier 3": "🔴"}
        st.metric(
            "Ülke Tier",
            f"{tier_colors.get(country_tier, '⚪')} {country_tier}"
        )

    st.markdown("---")

    # Niş analizi
    col4, col5 = st.columns(2)

    with col4:
        st.subheader("📈 Niş Değerlendirmesi")

        niche_quality = monetization.niche_profitability
        if niche_quality == "high":
            st.success(f"""
            **YÜKSEK DEĞER NİŞİ**

            {niche.upper()} sektörü reklamcılar için yüksek değerli.
            Banka, fintech, kripto reklamları premium ödüyor.
            """)
        elif niche_quality == "medium":
            st.warning(f"""
            **ORTA DEĞER NİŞİ**

            {niche.upper()} sektörü makul gelir potansiyeli taşıyor.
            """)
        else:
            st.error(f"""
            **DÜŞÜK DEĞER NİŞİ**

            {niche.upper()} sektöründe RPM düşük.
            Yüksek hacim gerekiyor.
            """)

        # Önerilen nişler
        if monetization.recommended_niches:
            st.subheader("💡 Önerilen Nişler")
            for rec_niche in monetization.recommended_niches:
                st.info(f"• {rec_niche}")

    with col5:
        st.subheader("🎯 Önerilen Stratejiler")
        for tip in monetization.tips:
            st.info(tip)

        # Uyarılar
        if monetization.warnings:
            st.subheader("⚠️ Uyarılar")
            for warning in monetization.warnings:
                st.warning(warning)

    st.markdown("---")

    # Mention stratejisi
    st.subheader("💡 GİZLİ BİLGİ: Mention Stratejisi")

    st.markdown("""
    Para kazanmanın gerçek yolu **mention'lar**dır:

    1. **Mention = Reklam Gösterimi**: Birini mention ettiğinizde, o kişi bildirimi açınca reklam görür
    2. **Zincir Etkisi**: Her mention yeni potansiyel reklam gösterimine dönüşür
    3. **Tartışma Başlatın**: İnsanların sizi mention etmesi için tartışmalı konulara girin

    **NOT:** Bu yüzden viral hesaplar sürekli mention topluyor!
    """)

    mention_tips = [
        "Sektör liderlerini etiketleyerek onay alın",
        "Tartışmalı konularda fikir belirtin",
        "Thread'lerde kullanıcıları mention edin",
        "Soru-cevap formatı kullanın"
    ]
    st.markdown("**Mention Artırma Taktikleri:**")
    for tip in mention_tips:
        st.success(f"✓ {tip}")

    st.markdown("---")

    # Türkiye özel uyarı
    if country == "TR":
        st.error("""
        **⚠️ TÜRKİYE İÇİN ÖNEMLİ UYARI**

        Türkiye Tier 3 ülke olduğu için RPM çok düşük ($0.05-0.5).

        **Seçenekler:**
        1. İngilizce içerik üretin → ABD/Avrupa kitlesine ulaşın
        2. Yüksek değerli nişlere yönelin (finans, kripto, trading)
        3. Hacim odaklı strateji → Çok tweet, çok mention
        4. Sponsorluk ve affiliate gelirlerine yönelin (X monetization'dan daha kârlı)
        """)

# Tab 5: Thread Oluştur (eski tab3)
with tab5:
    st.header("🧵 AI ile Thread Oluştur")

    if not generator.client:
        st.info("👈 Sol menüden **Anthropic API Key** girerek bu özelliği aktifleştirin.")
    else:
        thread_topic = st.text_input(
            "Thread Konusu:",
            placeholder="örn: Startup kurma rehberi...",
            key="thread_topic"
        )

        col1, col2 = st.columns(2)
        with col1:
            tweet_count = st.slider("Tweet Sayısı:", 3, 15, 7, key="thread_count")
        with col2:
            thread_style = st.selectbox(
                "Stil:",
                ["educational", "storytelling", "provocative"],
                format_func=lambda x: {
                    "educational": "🎓 Eğitici",
                    "storytelling": "📖 Hikaye",
                    "provocative": "🔥 Provokatif"
                }[x],
                key="thread_style"
            )

        if st.button("🧵 Thread Oluştur", type="primary", use_container_width=True, key="thread_btn"):
            if thread_topic:
                with st.spinner(f"🧵 {tweet_count} tweet'lik thread üretiliyor..."):
                    tweets = generator.generate_thread(thread_topic, tweet_count, thread_style)

                st.success(f"{len(tweets)} tweet'lik thread oluşturuldu!")

                for i, tweet in enumerate(tweets, 1):
                    with st.expander(f"Tweet {i}/{len(tweets)}", expanded=(i <= 2)):
                        st.text_area("", value=tweet, height=150, key=f"thread_tweet_{i}", label_visibility="collapsed")
                        st.caption(f"📏 {len(tweet)} karakter")
            else:
                st.warning("Lütfen bir konu girin.")

# Tab 6: Yeniden Yaz (eski tab4)
with tab6:
    st.header("✨ Tweet'i Yeniden Yaz")

    if not generator.client:
        st.info("👈 Sol menüden **Anthropic API Key** girerek bu özelliği aktifleştirin.")
    else:
        original_tweet = st.text_area(
            "Orijinal Tweet:",
            height=150,
            placeholder="Yeniden yazılacak tweet...",
            key="rewrite_original"
        )

        rewrite_style = st.selectbox(
            "Hedef Stil:",
            ["viral", "controversial", "emotional", "educational"],
            format_func=lambda x: {
                "viral": "🚀 Viral",
                "controversial": "⚡ Tartışmalı",
                "emotional": "💖 Duygusal",
                "educational": "🎓 Eğitici"
            }[x],
            key="rewrite_style"
        )

        if st.button("✨ Yeniden Yaz", type="primary", use_container_width=True, key="rewrite_btn"):
            if original_tweet:
                with st.spinner("✨ Tweet yeniden yazılıyor..."):
                    new_tweet = generator.rewrite_tweet(original_tweet, rewrite_style)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Öncesi")
                    st.text_area("", value=original_tweet, height=200, disabled=True, key="rewrite_before", label_visibility="collapsed")
                    orig_analysis = generator.analyze_tweet(original_tweet)
                    st.metric("Skor", f"{orig_analysis.score}/100")

                with col2:
                    st.subheader("Sonrası")
                    st.text_area("", value=new_tweet, height=200, key="rewrite_after", label_visibility="collapsed")
                    new_analysis = generator.analyze_tweet(new_tweet)
                    delta = new_analysis.score - orig_analysis.score
                    st.metric("Skor", f"{new_analysis.score}/100", delta=f"{delta:+.1f}")
            else:
                st.warning("Lütfen bir tweet yazın.")

# Tab 7: Şablonlar (eski tab5)
with tab7:
    st.header("📝 Viral Tweet Şablonları")

    categories = generator.get_template_categories()
    selected_category = st.selectbox("Kategori:", ["Tümü"] + categories, key="template_category")

    templates = generator.list_templates(
        category=selected_category if selected_category != "Tümü" else None
    )

    for t in templates:
        with st.expander(f"🔹 {t['name']} ({t['engagement_boost']}) [{t['category']}]"):
            st.markdown(f"**{t['description']}**")
            st.code(t['template'], language=None)

# Tab 8: Zamanlar (eski tab6)
with tab8:
    st.header("⏰ En İyi Paylaşım Zamanları")

    times = generator.get_best_posting_times()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📅 Hafta İçi")
        for time in times["weekdays"]:
            st.success(f"🕐 {time}")

    with col2:
        st.subheader("📅 Hafta Sonu")
        for time in times["weekends"]:
            st.info(f"🕐 {time}")

    with col3:
        st.subheader("🌟 Peak Zamanlar")
        for peak in times["peak_engagement"]:
            st.warning(f"🔥 {peak}")

    st.markdown("---")

    col4, col5 = st.columns(2)
    with col4:
        st.subheader("✅ En İyi Günler")
        for day in times["best_days"]:
            st.success(f"📌 {day}")

    with col5:
        st.subheader("❌ Kaçının")
        for avoid in times["avoid"]:
            st.error(f"⚠️ {avoid}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>X Algorithm Tweet Generator |
    <a href="https://github.com/ozerozcelik/x-tweet-generator" target="_blank">GitHub</a> |
    AI: Claude by Anthropic
    </p>
</div>
""", unsafe_allow_html=True)
