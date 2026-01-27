import { NextRequest, NextResponse } from "next/server"

// X Algorithm - Tweet Generation (from original working system)
// Source: tweet_generator.py - generate_with_ai method

interface UserProfile {
  followers: number
  following: number
  verified: boolean
  total_posts: number
  avg_like_rate: number
  account_age_years: number
  tweetcred_score?: number
}

interface TweetAnalysisResult {
  score: number
  rawScore: number
  maxScore: number
  distributionRate: number
  strengths: string[]
  weaknesses: string[]
  suggestions: string[]
  breakdown: {
    baseScore: number
    profileBoost: number
    contentBonus: number
    timingBonus: number
    viralBonus: number
    penalties: number[]
  }
  engagement_prediction: {
    favorite: number
    reply: number
    repost: number
    quote: number
    follow: number
  }
}

// ============================================
// AI GENERATION (Original Working Prompt)
// ============================================
async function generateWithAI(
  topic: string,
  style: string,
  tone: string,
  length: string,
  language: string,
  include_cta: boolean,
  profile?: UserProfile
): Promise<{ content: string; analysis: TweetAnalysisResult }> {
  const apiKey = process.env.ANTHROPIC_API_KEY

  if (!apiKey) {
    throw new Error("Anthropic API key not configured")
  }

  // Dil ayarları
  const languageConfig: Record<string, { name: string; instruction: string }> = {
    tr: { name: "Türkçe", instruction: "Tweet'i Türkçe yaz." },
    en: { name: "English", instruction: "Write the tweet in English." },
    de: { name: "Deutsch", instruction: "Write the tweet in German (Deutsch)." },
    fr: { name: "Français", instruction: "Write the tweet in French (Français)." },
    es: { name: "Español", instruction: "Write the tweet in Spanish (Español)." },
    ar: { name: "العربية", instruction: "Write the tweet in Arabic (العربية)." },
    zh: { name: "中文", instruction: "Write the tweet in Chinese (中文)." },
    ja: { name: "日本語", instruction: "Write the tweet in Japanese (日本語)." },
    ko: { name: "한국어", instruction: "Write the tweet in Korean (한국어)." },
    pt: { name: "Português", instruction: "Write the tweet in Portuguese (Português)." },
    ru: { name: "Русский", instruction: "Write the tweet in Russian (Русky)." },
  }

  // Prompt etiketleri (dile göre dinamik)
  const isTurkish = language === "tr"
  const labels = isTurkish ? {
    intro: "Sen X (Twitter) için viral tweet üreten bir AI asistanısın. Amaacın mümkün olan en yüksek etkileşimi alan tweet'i yazmak.",
    topic: "KONU",
    style: "STİL",
    tone: "TON",
    length: "UZUNLUK",
    profile_header: "👤 PROFİL",
    strategy: "STRATEJİ",
    verified: "OK",
    verified_advantage: "VERİFİED AVANTAJI:",
    divider: "═══════════════════════════════════════════════════════════════════",
    title: "🔥 2025 GÜNCELLENMİŞ X ALGORİTMASI - GROK PHOENIX",
    divider: "═══════════════════════════════════════════════════════════════════",
    grok_title: "GROK'UN NE ARADIĞI (2025 Güncel):",
    reply_gold: `"Reply" = Altın değer (1.5x) → Tartışma başlatan içerik ödül`,
    quote_strong: `"Quote Tweet" = En güçlü sinyal (2.5x) → Görüş + Amplifikasyon`,
    dwell: `"Dwell Time" = 3+ saniye okuma = Viral garantör`,
    follow: `"Follow_author" = Nihai hedef (5.0x) → Takipçi kazan`,
    viral_title: "VİRAL TWEET'LERİN ORTAK ÖZELLİKLERİ:",
    viral_1: `1. KUVGAR AÇILIŞI: "Kimse bunu bilmiyor..." → Merak = Scroll`,
    viral_2: `2. KARŞITLIK: "X diye düşünüyoruz ama aslında..." → Tartışma`,
    viral_3: `3. SAYILAR: "3 şey öğrendim..." → Değer algısı`,
    viral_4: `4. PERSONEL: "Bu hatayı yaptım ve..." -> Duygusal bağ`,
    viral_5: `5. ÖĞRETİCİ: "Bunu yapmayı bilmiyorsan..." → Fayda`,
    required_title: "YAPILMASI GEREKENLER (Viral için zorunlu):",
    req_hook: "✓ Hook ilk satırda - İlk 50 karakter kritik",
    req_space: "✓ 1-2 satır boşluk - Okunabilirlik için",
    req_question: "✓ En az 1 soru - Reply için",
    req_cta: "✓ Sonunda CTA - Etkileşim için",
    req_emoji: "✓ Emoji 1-3 adet - Dikkat çekici ama spam değil",
    forbidden_title: "YASAKLAR (Reach öldürücü):",
    forb_hashtag: "✗ Hashtag kullanma - Algoritma cezalandırır",
    forb_link: "✗ Dış link ekleme - -30% reach penaltısı",
    forb_follow4follow: "✗ 'Follow for follow' - Spam olarak işaretlenir",
    forb_caps: "✗ Tamamen büyük harf - Agresif olarak algılanır",
    forb_emoji_spam: "✗ 4+ emoji - Spam sinyali",
    improve_title: "İYİLEŞTİRME - ESKİSİNDEN FARKLAR:",
    imp_1: "1. Daha agresif opening: \"Bunu duymadın mı?\" yerine \"Bunu duymadıysan yalnız değilsin.\"",
    imp_2: "2. Sayılarla destek: \"3 yıl çalıştım, 50+ proje yaptım\" → Sosyal kanıt",
    imp_3: "3. \"Plot twist\" yap: \"Sonu hiç beklemedi...\" → Okuma devam et",
    imp_4: "4. Parantez içi konuşma: \"Arkadaşım şunu diyeyim...\" -> Samimiyet",
    imp_5: "5. Mizah kullan: Ama \"xD\" yerine 😄 kullan",
    imp_6: "6. Mevsucal format: \"1/\" → \"🧵 Thread\" başlığı ekle",
    cta_title: "CTA ÖNEMLİ: Son mutlaka aksiyon iste.",
    cta_reply: "• \"Ne düşünüyorsunuz?\" → Reply garantisi",
    cta_comment: "• \"Yorumlarda paylaşın\" → Amplifikasyon",
    cta_rt: "• \"Kaydetmek için RT\" → Repost teşviki",
    cta_follow: "• \"Follow edin daha fazlası için\" → Follow hedefi",
    final_instr: "TÜRKÇE YAZ, GRAMER KURALLARINA DİKKAT ET.",
    output_only: "Sadece tweet metni ver. Ek açıklama yapma.",
  } : {
    intro: "You are an AI assistant that generates viral tweets for X (Twitter). Your goal is to write tweets that get maximum engagement.",
    topic: "TOPIC",
    style: "STYLE",
    tone: "TONE",
    length: "LENGTH",
    profile_header: "👤 PROFILE",
    strategy: "STRATEGY",
    verified: "OK",
    verified_advantage: "VERIFIED ADVANTAGE:",
    divider: "═══════════════════════════════════════════════════════════════════",
    title: "🔥 2025 UPDATED X ALGORITHM - GROK PHOENIX",
    divider: "═══════════════════════════════════════════════════════════════════",
    grok_title: "WHAT GROK LOOKS FOR (2025 Updated):",
    reply_gold: `"Reply" = Golden value (1.5x) → Discussion starter reward`,
    quote_strong: `"Quote Tweet" = Strongest signal (2.5x) → Opinion + Amplification`,
    dwell: `"Dwell Time" = 3+ seconds reading = Viral guarantee`,
    follow: `"Follow_author" = Ultimate goal (5.0x) → Gain followers`,
    viral_title: "VIRAL TWEET COMMON PATTERNS:",
    viral_1: `1. POWERFUL OPENING: "Nobody knows this..." → Curiosity = Scroll stop`,
    viral_2: `2. CONTRARIAN: "We think X but actually..." → Discussion`,
    viral_3: `3. NUMBERS: "3 things I learned..." → Value perception`,
    viral_4: `4. PERSONAL: "I made this mistake and..." → Emotional connection`,
    viral_5: `5. EDUCATIONAL: "If you don't know how to..." → Value`,
    required_title: "REQUIRED FOR VIRALITY:",
    req_hook: "✓ Hook in first line - First 50 characters critical",
    req_space: "✓ 1-2 line breaks - For readability",
    req_question: "✓ At least 1 question - For replies",
    req_cta: "✓ CTA at end - For engagement",
    req_emoji: "✓ 1-3 emojis - Eye-catching but not spam",
    forbidden_title: "FORBIDDEN (Kills reach):",
    forb_hashtag: "✗ No hashtags - Algorithm penalizes",
    forb_link: "✗ No external links - -30% reach penalty",
    forb_follow4follow: "✗ No 'follow for follow' - Marked as spam",
    forb_caps: "✗ No all caps - Perceived as aggressive",
    forb_emoji_spam: "✗ 4+ emojis - Spam signal",
    improve_title: "IMPROVEMENTS OVER OLD SYSTEM:",
    imp_1: "1. More aggressive opening: Instead of \"Did you hear?\" use \"If you haven't heard this, you're not alone.\"",
    imp_2: "2. Support with numbers: \"Worked 3 years, did 50+ projects\" → Social proof",
    imp_3: "3. Use \"plot twist\": \"You won't believe the ending...\" → Keep reading",
    imp_4: "4. Parenthetical talk: \"My friend let me tell you...\" → Authenticity",
    imp_5: "5. Use humor: But use 😄 instead of \"xD\"",
    imp_6: "6. Thread format: \"1/\" → Add \"🧵 Thread\" header",
    cta_title: "CTA IMPORTANT: Always include action at the end.",
    cta_reply: "• \"What do you think?\" → Reply guarantee",
    cta_comment: "• \"Share in comments\" → Amplification",
    cta_rt: "• \"RT to save\" → Repost incentive",
    cta_follow: "• \"Follow for more\" → Follow goal",
    final_instr: `Write in ${languageConfig[language]?.name || "English"}.`,
    output_only: "Only provide the tweet text. No additional explanation.",
  }

  // Profil bazlı strateji
  let profileStrategy = ""
  if (profile) {
    const followers = profile.followers
    const isVerified = profile.verified

    if (followers < 1000) {
      profileStrategy = isTurkish ? `
👤 PROFİL: BÜYÜME AŞAMASI (< 1K takipçi)
STRATEJİ:
- Viral potansiyeli YÜKSEK içerik üret (paylaşılabilir, relatable)
- Soru sor, tartışma başlat → Reply ve RT al
- Trending konulara değin → Keşfet'e düş
- Niche topluluklara hitap et → Sadık takipçi kazan
- Hook çok güçlü olmalı → Scroll durdur
- Kişisel hikaye ve deneyim paylaş → Bağ kur
- "Follow için sebep ver" mantığı → Değer sun
` : `
👤 PROFILE: GROWTH STAGE (< 1K followers)
STRATEGY:
- Create HIGH viral potential content (shareable, relatable)
- Ask questions, start discussions → Get replies and RTs
- Tap into trending topics → Hit Explore
- Target niche communities → Build loyal following
- Hook must be very strong → Stop the scroll
- Share personal stories and experiences → Build connection
- "Give a reason to follow" mindset → Provide value
`
    } else if (followers < 10000) {
      profileStrategy = isTurkish ? `
👤 PROFİL: GELİŞME AŞAMASI (1K-10K takipçi)
STRATEJİ:
- Tutarlı içerik üret → Marka oluştur
- Thread formatı kullan → Derin değer sun
- Engagement'ı koru → Mevcut kitleyi kaybetme
- Niche'te otorite ol → Spesifik konularda derinleş
- Diğer hesaplarla etkileşim → Networking
- Quote tweet ile görüş bildir → Görünürlük
` : `
👤 PROFILE: GROWTH STAGE (1K-10K followers)
STRATEGY:
- Consistent content creation → Build your brand
- Use thread format → Provide deep value
- Maintain engagement → Don't lose existing audience
- Become authority in niche → Deep dive in specific topics
- Engage with other accounts → Network
- Quote tweet to share opinions → Visibility
`
    } else if (followers < 100000) {
      profileStrategy = isTurkish ? `
👤 PROFİL: MİD-TİER (10K-100K takipçi)
STRATEJİ:
- Otoriter ve güvenilir ton kullan
- Değer odaklı içerik → Kaliteyi koru
- Kendi görüşlerini cesurca paylaş
- Trend belirleyici ol, takip etme
- Thread ve uzun içerik → Dwell time
- Tartışmalı konularda pozisyon al
` : `
👤 PROFILE: MID-TIER (10K-100K followers)
STRATEGY:
- Use authoritative and credible tone
- Value-focused content → Maintain quality
- Share your opinions boldly
- Be a trendsetter, not a follower
- Threads and long-form → Dwell time
- Take positions on controversial topics
`
    } else {
      profileStrategy = isTurkish ? `
👤 PROFİL: BÜYÜK HESAP (100K+ takipçi)
STRATEJİ:
- Otorite ve liderlik tonu
- Orijinal düşünce ve içgörü sun
- Kısa, vurucu mesajlar da işe yarar (zaten görünürlüğün var)
- Topluluk oluştur, kitleyi yönlendir
- Marka değerini koru, tartışmalı konularda dikkatli ol
- Diğer büyük hesaplarla etkileşim
` : `
👤 PROFILE: LARGE ACCOUNT (100K+ followers)
STRATEGY:
- Authority and leadership tone
- Share original thought and insight
- Short, punchy messages also work (you already have visibility)
- Build community, guide your audience
- Protect brand value, be careful on controversial topics
- Engage with other large accounts
`
    }

    if (isVerified) {
      profileStrategy += isTurkish ? `
[${labels.verified}] ${labels.verified_advantage}
- TweetCred +100 boost → Daha geniş dağıtım
- Duplicate content'te %30 muafiyet
- Daha cesur ve tartışmalı olabilirsin
- Otorite sinyalleri güçlü
` : `
[${labels.verified}] ${labels.verified_advantage}
- TweetCred +100 boost → Wider distribution
- 30% exemption on duplicate content
- You can be bolder and more controversial
- Authority signals are strong
`
    }
  }

  // Uzunluk rehberi (dile göre dinamik)
  const lengthGuide: Record<string, string> = isTurkish ? {
    short: "100-200 karakter",
    medium: "300-600 karakter",
    long: "800-1500 karakter",
    epic: "2000-4000 karakter (X Premium için)",
  } : {
    short: "100-200 characters",
    medium: "300-600 characters",
    long: "800-1500 characters",
    epic: "2000-4000 characters (X Premium)",
  }

  // Stil rehberi (dile göre dinamik)
  const styleGuide: Record<string, string> = isTurkish ? {
    professional: "Profesyonel ve bilgili, otorite sahibi",
    casual: "Samimi ve rahat, arkadaşça",
    provocative: "Kışkırtıcı ve düşündürücü, status quo'yu sorgulayan",
    story: "Hikaye anlatıcı, duygusal bağ kuran",
    storytelling: "Hikaye anlatıcı, duygusal bağ kuran",
    educational: "Öğretici, değer veren, framework sunan",
    motivational: "İlham verici ve motive edici",
    list: "Liste formatı, madde madde",
    question: "Soru odaklı, etkileşim teşvik edici",
    controversial: "Tartışmalı, cesur, karşıt görüş",
  } : {
    professional: "Professional and knowledgeable, authoritative",
    casual: "Friendly and relaxed, casual",
    provocative: "Provocative and thought-provoking, questions status quo",
    story: "Storyteller, creates emotional connection",
    storytelling: "Storyteller, creates emotional connection",
    educational: "Educational, provides value, shares frameworks",
    motivational: "Inspiring and motivating",
    list: "List format, bullet points",
    question: "Question-focused, encourages engagement",
    controversial: "Controversial, bold, contrarian views",
  }

  // Ton rehberi (dile göre dinamik)
  const toneGuide: Record<string, string> = isTurkish ? {
    engaging: "Dikkat çekici ve etkileşim odaklı",
    controversial: "Tartışmalı ve cesur, karşıt görüş",
    inspirational: "İlham verici ve motive edici",
    humorous: "Esprili ve eğlenceli",
    raw: "Ham, dürüst, filtresiz",
  } : {
    engaging: "Attention-grabbing and engagement-focused",
    controversial: "Controversial and bold, contrarian views",
    inspirational: "Inspiring and motivating",
    humorous: "Witty and entertaining",
    raw: "Unfiltered, honest, raw",
  }

  // Prompt oluştur (İYİLEŞTİRMİŞ - DİNAMİK DİL DESTEĞİ)
  const prompt = `${labels.intro}

${labels.topic}: ${topic}
${labels.style}: ${style} - ${styleGuide[style] || style}
${labels.tone}: ${tone} - ${toneGuide[tone] || tone}
${labels.length}: ${lengthGuide[length] || length}
${profileStrategy}

${labels.divider}
${labels.title}
${labels.divider}

${labels.grok_title}
- ${labels.reply_gold}
- ${labels.quote_strong}
- ${labels.dwell}
- ${labels.follow}

${labels.viral_title}
${labels.viral_1}
${labels.viral_2}
${labels.viral_3}
${labels.viral_4}
${labels.viral_5}

${labels.required_title}
${labels.req_hook}
${labels.req_space}
${labels.req_question}
${labels.req_cta}
${labels.req_emoji}

${labels.forbidden_title}
${labels.forb_hashtag}
${labels.forb_link}
${labels.forb_follow4follow}
${labels.forb_caps}
${labels.forb_emoji_spam}

${labels.improve_title}
${labels.imp_1}
${labels.imp_2}
${labels.imp_3}
${labels.imp_4}
${labels.imp_5}
${labels.imp_6}

${include_cta ? `${labels.cta_title}
${labels.cta_reply}
${labels.cta_comment}
${labels.cta_rt}
${labels.cta_follow}` : ""}

${labels.final_instr}

${labels.output_only}`

  // Max tokens ayarla
  const maxTokensMap: Record<string, number> = {
    short: 1000,
    medium: 2000,
    long: 4000,
    epic: 8000,
  }
  const tokens = maxTokensMap[length] || 2000

  // API çağrısı
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: tokens,
      messages: [{ role: "user", content: prompt }],
    }),
  })

  if (!response.ok) {
    const error = await response.text()
    console.error("Anthropic API error:", error)
    throw new Error("AI generation failed")
  }

  const data = await response.json()
  const content = data.content?.[0]?.text || ""

  // Clean up
  const cleanedContent = content.trim()

  // Skor hesapla
  const analysis = calculateScore(cleanedContent, profile)

  return { content: cleanedContent, analysis }
}

// ============================================
// SCORE CALCULATION
// ============================================
function calculateScore(content: string, profile?: UserProfile): TweetAnalysisResult {
  const length = content.length
  let score = 50

  // Uzunluk
  if (length >= 60 && length <= 220) score += 15
  else if (length >= 40 && length <= 280) score += 10

  // Özellikler
  const hasQuestion = content.includes("?")
  const emojiCount = (content.match(/[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu) || []).length
  const hasNewlines = content.includes("\n")
  const hashtagCount = (content.match(/#/g) || []).length
  const hasLink = content.includes("http")

  if (hasQuestion) score += 15
  if (emojiCount >= 1 && emojiCount <= 3) score += 10
  if (hasNewlines) score += 10
  if (!hasLink) score += 15

  // Viral indicators
  const viralKeywords = ["tartışmalı", "garip", "yanlış", "aslında", "haber", "gelişme"]
  if (viralKeywords.some(k => content.toLowerCase().includes(k))) score += 10

  // Penalties
  if (emojiCount > 5) score -= 15
  if (hashtagCount > 3) score -= 15
  if (hasLink) score -= 20
  if (length > 25000) score -= 10  // X Premium max limit

  // Clamp
  score = Math.max(0, Math.min(100, score))

  // Engagement prediction
  const engagement_prediction = {
    favorite: 0.02 + (score / 100) * 0.08,
    reply: 0.005 + (hasQuestion ? 0.025 : 0.005) + (score / 100) * 0.03,
    repost: 0.003 + (score / 100) * 0.02,
    quote: 0.002 + (score / 100) * 0.015,
    follow: (score / 100) * 0.02 + (profile?.verified ? 0.01 : 0),
  }

  // Strengths & Weaknesses
  const strengths: string[] = []
  const weaknesses: string[] = []
  const suggestions: string[] = []

  if (hasQuestion) strengths.push("Soru içeriyor (reply teşviki)")
  if (!hasLink) strengths.push("Dış link yok")
  if (emojiCount >= 1 && emojiCount <= 3) strengths.push("Emoji kullanımı iyi")
  if (hasNewlines) strengths.push("Satır araları var (dwell time)")

  if (hasLink) weaknesses.push("Dış link içeriyor")
  if (emojiCount > 5) weaknesses.push("Çok emoji")
  if (hashtagCount > 3) weaknesses.push("Çok hashtag")
  if (!hasQuestion) suggestions.push("Soru ekleyin")

  return {
    score: Math.round(score),
    rawScore: score,
    maxScore: 100,
    distributionRate: profile ? 0.8 : 0.5,
    strengths,
    weaknesses,
    suggestions,
    breakdown: {
      baseScore: score,
      profileBoost: profile && profile.verified ? 1.2 : 1.0,
      contentBonus: 1.0,
      timingBonus: 1.0,
      viralBonus: 1.0,
      penalties: [],
    },
    engagement_prediction,
  }
}

// ============================================
// API ENDPOINT
// ============================================
export async function POST(req: NextRequest) {
  try {
    const {
      topic,
      style = "casual",
      tone = "engaging",
      length = "medium",
      language = "tr",
      include_cta = true,
      include_emoji = true,
      userProfile,
    } = await req.json()

    if (!topic) {
      return NextResponse.json({ error: "Topic is required" }, { status: 400 })
    }

    const result = await generateWithAI(
      topic,
      style,
      tone,
      length,
      language,
      include_cta,
      userProfile
    )

    return NextResponse.json({
      content: result.content,
      analysis: result.analysis,
    })
  } catch (error) {
    console.error("Tweet generation error:", error)
    const errorMessage = error instanceof Error ? error.message : "AI generation failed"
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 },
    )
  }
}
