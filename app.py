"""
X Algorithm Tweet Generator - Web Interface
Streamlit ile oluşturulmuş web arayüzü
"""

import streamlit as st
import json
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
        margin-bottom: 2rem;
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
    .template-card {
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .stTextArea textarea {
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Generator instance
generator = XAlgorithmTweetGenerator()

# Header
st.markdown('<p class="main-header">🐦 X Algorithm Tweet Generator</p>', unsafe_allow_html=True)
st.markdown("*X algoritmasına göre tweet'lerinizi optimize edin*")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Tweet Analizi",
    "📝 Şablonlar",
    "✨ Optimize Et",
    "💡 Öneri Al",
    "⏰ En İyi Zamanlar"
])

# Tab 1: Tweet Analizi
with tab1:
    st.header("Tweet Analizi")
    st.markdown("Tweet'inizi yazın, algoritma skoru ve önerileri görün.")

    tweet_input = st.text_area(
        "Tweet'inizi yazın:",
        height=150,
        placeholder="Tweet metninizi buraya yazın...",
        max_chars=280
    )

    char_count = len(tweet_input)
    st.caption(f"📏 {char_count}/280 karakter")

    if st.button("🔍 Analiz Et", type="primary", use_container_width=True):
        if tweet_input.strip():
            analysis = generator.analyze_tweet(tweet_input)

            col1, col2 = st.columns([1, 2])

            with col1:
                # Skor gösterimi
                score = analysis.score
                if score >= 90:
                    score_class = "score-high"
                    emoji = "🚀"
                elif score >= 70:
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

                # Engagement tahmini
                st.subheader("📈 Engagement Tahmini")
                for action, prob in analysis.engagement_prediction.items():
                    st.progress(prob, text=f"{action}: {prob*100:.0f}%")

            with col2:
                # Güçlü yönler
                if analysis.strengths:
                    st.subheader("✅ Güçlü Yönler")
                    for s in analysis.strengths:
                        st.success(s)

                # Zayıf yönler
                if analysis.weaknesses:
                    st.subheader("❌ Zayıf Yönler")
                    for w in analysis.weaknesses:
                        st.error(w)

                # Öneriler
                if analysis.suggestions:
                    st.subheader("💡 Öneriler")
                    for s in analysis.suggestions:
                        st.info(s)
        else:
            st.warning("Lütfen bir tweet yazın.")

# Tab 2: Şablonlar
with tab2:
    st.header("Viral Tweet Şablonları")
    st.markdown("Yüksek engagement şablonlarından birini seçin ve özelleştirin.")

    templates = generator.list_templates()

    selected_template = st.selectbox(
        "Şablon seçin:",
        options=[t["name"] for t in templates],
        format_func=lambda x: f"{x} ({next(t['engagement_boost'] for t in templates if t['name'] == x)} boost)"
    )

    # Seçilen şablon bilgisi
    template_info = next(t for t in templates if t["name"] == selected_template)
    st.info(f"📌 {template_info['description']}")
    st.code(template_info['template'], language=None)

    st.markdown("---")
    st.subheader("Şablonu Doldur")

    # Şablon değişkenlerini çıkar
    import re
    template_text = template_info['template']
    variables = re.findall(r'\{(\w+)\}', template_text)

    var_values = {}
    cols = st.columns(2)
    for i, var in enumerate(variables):
        with cols[i % 2]:
            var_values[var] = st.text_input(f"{var}:", key=f"var_{var}")

    if st.button("🐦 Tweet Oluştur", type="primary", use_container_width=True):
        if all(var_values.values()):
            generated_tweet = generator.generate_from_template(selected_template, var_values)
            st.success("Tweet oluşturuldu!")
            st.text_area("Oluşturulan Tweet:", value=generated_tweet, height=150)
            st.caption(f"📏 {len(generated_tweet)}/280 karakter")

            # Kopyalama butonu
            st.code(generated_tweet, language=None)
        else:
            st.warning("Lütfen tüm alanları doldurun.")

# Tab 3: Optimize Et
with tab3:
    st.header("Tweet Optimizasyonu")
    st.markdown("Mevcut tweet'inizi algoritma için optimize edin.")

    original_tweet = st.text_area(
        "Orijinal tweet:",
        height=150,
        placeholder="Optimize edilecek tweet...",
        key="optimize_input"
    )

    if st.button("✨ Optimize Et", type="primary", use_container_width=True):
        if original_tweet.strip():
            optimized = generator.optimize_tweet(original_tweet)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Öncesi")
                st.text_area("", value=original_tweet, height=150, disabled=True, key="before")
                original_analysis = generator.analyze_tweet(original_tweet)
                st.metric("Skor", f"{original_analysis.score}/100")

            with col2:
                st.subheader("Sonrası")
                st.text_area("", value=optimized, height=150, key="after")
                optimized_analysis = generator.analyze_tweet(optimized)
                delta = optimized_analysis.score - original_analysis.score
                st.metric("Skor", f"{optimized_analysis.score}/100", delta=f"{delta:+.1f}")

            st.markdown("---")
            st.subheader("📋 Kopyala")
            st.code(optimized, language=None)
        else:
            st.warning("Lütfen bir tweet yazın.")

# Tab 4: Öneri Al
with tab4:
    st.header("Konu Önerileri")
    st.markdown("Bir konu girin, farklı stilde tweet önerileri alın.")

    col1, col2 = st.columns([2, 1])

    with col1:
        topic = st.text_input("Konu:", placeholder="örn: yapay zeka, startup, kariyer...")

    with col2:
        style = st.selectbox(
            "Stil:",
            options=["professional", "casual", "provocative"],
            format_func=lambda x: {
                "professional": "🎩 Profesyonel",
                "casual": "😎 Casual",
                "provocative": "🔥 Provokatif"
            }[x]
        )

    if st.button("💡 Öneri Al", type="primary", use_container_width=True):
        if topic.strip():
            suggestions = generator.suggest_improvements(topic, style)

            for i, suggestion in enumerate(suggestions, 1):
                with st.expander(f"Öneri {i}", expanded=True):
                    st.text_area("", value=suggestion, height=120, key=f"suggestion_{i}")
                    st.caption(f"📏 {len(suggestion)}/280 karakter")
        else:
            st.warning("Lütfen bir konu girin.")

# Tab 5: En İyi Zamanlar
with tab5:
    st.header("En İyi Paylaşım Zamanları")
    st.markdown("Tweet'lerinizi ne zaman paylaşmalısınız?")

    times = generator.get_best_posting_times()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Hafta İçi")
        for time in times["weekdays"]:
            st.success(f"🕐 {time}")

        st.subheader("🌟 En İyi Günler")
        for day in times["best_days"]:
            st.info(f"📌 {day}")

    with col2:
        st.subheader("📅 Hafta Sonu")
        for time in times["weekends"]:
            st.success(f"🕐 {time}")

        st.subheader("⚠️ Kaçının")
        for avoid in times["avoid"]:
            st.warning(f"❌ {avoid}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>X Algorithm Tweet Generator |
    <a href="https://github.com/ozerozcelik/x-tweet-generator" target="_blank">GitHub</a> |
    Based on <a href="https://github.com/xai-org/x-algorithm" target="_blank">X Algorithm</a>
    </p>
</div>
""", unsafe_allow_html=True)
