"""
X Algorithm Tweet Generator - Web Interface
AI-Powered with Claude API + Profile Analysis
"""

import streamlit as st
import os
from tweet_generator import XAlgorithmTweetGenerator, XProfileAnalyzer

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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🤖 AI Tweet Üret",
    "📊 Tweet Analizi",
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

# Tab 3: Thread Oluştur
with tab3:
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

# Tab 4: Yeniden Yaz
with tab4:
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

# Tab 5: Şablonlar
with tab5:
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

# Tab 6: Zamanlar
with tab6:
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
