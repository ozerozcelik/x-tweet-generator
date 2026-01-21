"""
X Algorithm Tweet Generator - Web Interface
AI-Powered with Claude API
"""

import streamlit as st
import os
from tweet_generator import XAlgorithmTweetGenerator

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
        margin-left: 0.5rem;
    }
    .stTextArea textarea { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# Session state
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

# Sidebar - API Ayarları
with st.sidebar:
    st.header("⚙️ Ayarlar")

    api_key = st.text_input(
        "Anthropic API Key",
        value=st.session_state.api_key,
        type="password",
        help="Claude AI için API key gerekli"
    )
    st.session_state.api_key = api_key

    is_premium = st.checkbox("X Premium Hesabı", value=True, help="25,000 karakter limiti")

    st.markdown("---")
    st.markdown("### 📊 X Algoritması")
    st.markdown("""
    **Pozitif Sinyaller:**
    - Reply > Repost > Like
    - Thread formatı
    - Uzun form içerik

    **Negatif Sinyaller:**
    - Dış linkler
    - Çok hashtag
    - Spam kelimeler
    """)

    if api_key:
        st.success("✅ AI aktif")
    else:
        st.warning("⚠️ AI için API key girin")

# Generator instance
generator = XAlgorithmTweetGenerator(api_key=st.session_state.api_key, is_premium=is_premium)

# Header
st.markdown('<p class="main-header">🐦 X Algorithm Tweet Generator</p>', unsafe_allow_html=True)
if generator.client:
    st.markdown('<p style="text-align:center;"><span class="ai-badge">🤖 AI Powered</span></p>', unsafe_allow_html=True)

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
        st.warning("Bu özellik için sol menüden Anthropic API Key girin.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            topic = st.text_input("Konu:", placeholder="örn: yapay zeka, startup, kariyer...")

        with col2:
            length = st.selectbox("Uzunluk:", ["short", "medium", "long", "epic"],
                                 format_func=lambda x: {
                                     "short": "📝 Kısa (100-200)",
                                     "medium": "📄 Orta (300-600)",
                                     "long": "📰 Uzun (800-1500)",
                                     "epic": "📚 Epik (2000-4000)"
                                 }[x], index=1)

        col3, col4 = st.columns(2)
        with col3:
            style = st.selectbox("Stil:", ["professional", "casual", "provocative", "storytelling", "educational"],
                                format_func=lambda x: {
                                    "professional": "🎩 Profesyonel",
                                    "casual": "😎 Casual",
                                    "provocative": "🔥 Provokatif",
                                    "storytelling": "📖 Hikaye",
                                    "educational": "🎓 Eğitici"
                                }[x])
        with col4:
            tone = st.selectbox("Ton:", ["engaging", "controversial", "inspirational", "humorous", "raw"],
                               format_func=lambda x: {
                                   "engaging": "💬 Etkileşimci",
                                   "controversial": "⚡ Tartışmalı",
                                   "inspirational": "✨ İlham Verici",
                                   "humorous": "😄 Esprili",
                                   "raw": "💯 Ham/Dürüst"
                               }[x])

        col5, col6 = st.columns(2)
        with col5:
            include_cta = st.checkbox("Call to Action ekle", value=True)
        with col6:
            include_emoji = st.checkbox("Emoji kullan", value=True)

        custom_instructions = st.text_area("Özel talimatlar (opsiyonel):", height=80,
                                          placeholder="örn: Benim sektörüm fintech, hedef kitle yatırımcılar...")

        if st.button("🚀 Tweet Üret", type="primary", use_container_width=True):
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
                st.text_area("Üretilen Tweet:", value=tweet, height=250)
                st.caption(f"📏 {len(tweet)} karakter")

                # Analiz et
                analysis = generator.analyze_tweet(tweet)
                st.metric("Algoritma Skoru", f"{analysis.score}/100")
            else:
                st.warning("Lütfen bir konu girin.")

# Tab 2: Tweet Analizi
with tab2:
    st.header("📊 Tweet Analizi")

    tweet_input = st.text_area(
        "Tweet'inizi yazın:",
        height=200,
        placeholder="Analiz edilecek tweet...",
        key="analyze_input"
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
                st.subheader("📈 Engagement Tahmini")
                for action, prob in analysis.engagement_prediction.items():
                    st.progress(prob, text=f"{action}: {prob*100:.0f}%")

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
        else:
            st.warning("Lütfen bir tweet yazın.")

# Tab 3: Thread Oluştur
with tab3:
    st.header("🧵 AI ile Thread Oluştur")

    if not generator.client:
        st.warning("Bu özellik için sol menüden Anthropic API Key girin.")
    else:
        thread_topic = st.text_input("Thread Konusu:", placeholder="örn: Startup kurma rehberi...")

        col1, col2 = st.columns(2)
        with col1:
            tweet_count = st.slider("Tweet Sayısı:", 3, 15, 7)
        with col2:
            thread_style = st.selectbox("Stil:", ["educational", "storytelling", "provocative"],
                                       format_func=lambda x: {
                                           "educational": "🎓 Eğitici",
                                           "storytelling": "📖 Hikaye",
                                           "provocative": "🔥 Provokatif"
                                       }[x], key="thread_style")

        if st.button("🧵 Thread Oluştur", type="primary", use_container_width=True):
            if thread_topic:
                with st.spinner(f"🧵 {tweet_count} tweet'lik thread üretiliyor..."):
                    tweets = generator.generate_thread(thread_topic, tweet_count, thread_style)

                st.success(f"{len(tweets)} tweet'lik thread oluşturuldu!")

                for i, tweet in enumerate(tweets, 1):
                    with st.expander(f"Tweet {i}/{len(tweets)}", expanded=(i <= 2)):
                        st.text_area("", value=tweet, height=150, key=f"thread_{i}", label_visibility="collapsed")
                        st.caption(f"📏 {len(tweet)} karakter")
            else:
                st.warning("Lütfen bir konu girin.")

# Tab 4: Yeniden Yaz
with tab4:
    st.header("✨ Tweet'i Yeniden Yaz")

    if not generator.client:
        st.warning("Bu özellik için sol menüden Anthropic API Key girin.")
    else:
        original_tweet = st.text_area("Orijinal Tweet:", height=150, placeholder="Yeniden yazılacak tweet...")

        rewrite_style = st.selectbox("Hedef Stil:", ["viral", "controversial", "emotional", "educational"],
                                    format_func=lambda x: {
                                        "viral": "🚀 Viral",
                                        "controversial": "⚡ Tartışmalı",
                                        "emotional": "💖 Duygusal",
                                        "educational": "🎓 Eğitici"
                                    }[x])

        if st.button("✨ Yeniden Yaz", type="primary", use_container_width=True):
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
    selected_category = st.selectbox("Kategori:", ["Tümü"] + categories)

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
