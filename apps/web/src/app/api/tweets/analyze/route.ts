import { NextRequest, NextResponse } from "next/server"

// ============================================
// X PHOENIX ALGORITHM - Complete Implementation
// Shared scoring logic for both generate and analyze
// ============================================

// --- ACTION WEIGHTS (Grok-calibrated) ---
const ACTION_WEIGHTS = {
  reply: 1.5, quote: 1.3, repost: 1.2, share: 1.2, follow_author: 5.0,
  profile_click: 0.8, video_view: 1.0, photo_expand: 0.7, click: 0.5, favorite: 0.3,
  dwell: 1.0, not_interested: -2.0, block_author: -3.0, mute_author: -2.5, report: -5.0,
}

const CONTENT_MULTIPLIERS = {
  text_only: 1.0, with_image: 1.4, with_video: 1.8, with_poll: 1.6,
  thread: 1.25, reply: 0.5, quote: 1.1, with_link: 0.7,
}

const VIRAL_FACTORS = {
  controversial_topic: 2.2, breaking_news: 2.8, trending_hashtag: 1.8,
  celebrity_mention: 1.8, humor: 1.6, relatable: 1.4, educational: 1.25,
  personal_story: 1.3, debate_starter: 2.0,
}

const TWEETCRED_DEFAULT = -128
const TWEETCRED_MIN_POSITIVE = 17
const TWEETCRED_COLD_START = -50
const ENGAGEMENT_DEBT_POSTS = 100
const MAX_DAILY_POSTS_OPTIMAL = 2

interface TweetAnalysisResult {
  score: number
  rawScore: number
  maxScore: number
  distributionRate: number
  strengths: string[]
  weaknesses: string[]
  suggestions: string[]
  warnings?: string[]
  breakdown: {
    baseScore: number
    profileBoost: number
    contentBonus: number
    timingBonus: number
    viralBonus: number
    authorDiversityPenalty: number
    penalties: number[]
  }
  engagement_prediction: {
    favorite: number; reply: number; repost: number; quote: number; follow: number
    click: number; profile_click: number; video_view: number; photo_expand: number
    share: number; dwell: number; not_interested: number; block: number; mute: number; report: number
  }
  phoenix_insights: {
    candidate_isolation_ready: boolean
    golden_hour_status: string
    author_diversity_status: string
    tweetcred_status: string
    engagement_debt_status: string
  }
}

// Tweet Analysis - X Phoenix Algorithm
export async function POST(req: NextRequest) {
  const { content, userProfile } = await req.json()

  if (!content || typeof content !== "string") {
    return NextResponse.json({ error: "Content is required" }, { status: 400 })
  }

  // Phoenix skor hesapla
  const analysis = calculatePhoenixScore(content, userProfile)

  return NextResponse.json(analysis)
}

function calculatePhoenixScore(content: string, profile?: any): TweetAnalysisResult {
  const length = content.length
  let baseScore = 50

  // Uzunluk skoru
  if (length >= 60 && length <= 220) baseScore += 15
  else if (length >= 40 && length <= 280) baseScore += 10

  // Özellikler
  const hasQuestion = content.includes("?")
  const emojiCount = (content.match(/[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu) || []).length
  const hasNewlines = content.includes("\n")
  const hashtagCount = (content.match(/#/g) || []).length
  const hasLink = content.includes("http")

  // Reply incentives (Phoenix: reply = highest weight)
  if (hasQuestion) baseScore += 15
  if (emojiCount >= 1 && emojiCount <= 3) baseScore += 8
  if (hasNewlines) baseScore += 5
  if (!hasLink) baseScore += 12

  const isLongForm = length > 150 || hasNewlines
  if (isLongForm) baseScore += 10  // Dwell time potential

  // Penalties
  if (emojiCount > 5) baseScore -= 20
  if (hashtagCount > 3) baseScore -= 15
  if (hasLink) baseScore -= 15
  if (length > 25000) baseScore -= 25  // X Premium max limit

  // Profile Boost
  let profileBoost = 1.0
  let distributionRate = 0.5

  if (profile) {
    const tweetcred = profile.tweetcred_score || TWEETCRED_DEFAULT
    if (tweetcred >= TWEETCRED_MIN_POSITIVE) {
      distributionRate = 1.0
    } else if (tweetcred <= TWEETCRED_COLD_START) {
      distributionRate = 0.10
    } else {
      distributionRate = 0.3 + ((tweetcred + 50) / 150)
    }
    if (profile.verified) profileBoost += 1.2
  }

  // Content Type Bonus
  let contentBonus = 1.0
  if (content.includes("🧵") || content.includes("1/") || content.includes("1.")) {
    contentBonus = CONTENT_MULTIPLIERS.thread
  }
  if (hasLink) contentBonus = CONTENT_MULTIPLIERS.with_link

  // Viral Boosters Detection
  const viralKeywords = {
    controversial: ["bence", "sanmıyorum", "tartışmaya açığım", "garip", "yanlış", "katılmıyorum"],
    breaking_news: ["haber", "gelişme", "başladı", "anında", "yeni", "son dakika"],
    trending: ["trend", "popüler", "viral", "gündem"],
    educational: ["öğren", "bilmeniz gereken", "nasıl", "nedir", "neden"],
    relatable: ["herkesin yaşar", "hepimiz", "birçokumuz", "hayat kavgası", "yalnız değilsiniz"],
    humor: ["😂", "😄", "😅", "🤣"],
    debate: ["ne düşünüyorsunuz", "sizce", "katılıyor musunuz", "tartışalım"],
  }

  let viralBonus = 1.0
  if (viralKeywords.controversial.some(k => content.toLowerCase().includes(k))) viralBonus += VIRAL_FACTORS.controversial_topic - 1
  if (viralKeywords.breaking_news.some(k => content.toLowerCase().includes(k))) viralBonus += VIRAL_FACTORS.breaking_news - 1
  if (viralKeywords.trending.some(k => content.toLowerCase().includes(k))) viralBonus += VIRAL_FACTORS.trending_hashtag - 1
  if (viralKeywords.educational.some(k => content.toLowerCase().includes(k))) viralBonus += VIRAL_FACTORS.educational - 1
  if (viralKeywords.relatable.some(k => content.toLowerCase().includes(k))) viralBonus += VIRAL_FACTORS.relatable - 1
  if (viralKeywords.debate.some(k => content.toLowerCase().includes(k))) viralBonus += VIRAL_FACTORS.debate_starter - 1
  if (viralKeywords.humor.some(e => content.includes(e))) viralBonus += VIRAL_FACTORS.humor - 1

  // Author Diversity Penalty
  let authorDiversityPenalty = 1.0
  const warnings: string[] = []
  if (profile?.recent_post_count && profile.recent_post_count > MAX_DAILY_POSTS_OPTIMAL) {
    const excessPosts = profile.recent_post_count - MAX_DAILY_POSTS_OPTIMAL
    authorDiversityPenalty = Math.max(0.4, 1.0 - (excessPosts * 0.15))
    warnings.push(`${profile.recent_post_count} post attın (optimal: 2)`)
  }

  // Timing Bonus
  let timingBonus = 1.0
  const now = new Date()
  const hour = now.getHours()
  const day = now.getDay()
  if ((hour >= 18 && hour <= 21) || (hour >= 12 && hour <= 13)) timingBonus = 1.2
  if (hour >= 0 && hour <= 6) timingBonus = 0.7
  if (day >= 1 && day <= 4) timingBonus *= 1.1
  if (day === 0) timingBonus *= 0.8

  // Penalties
  const penalties: number[] = []
  if (length > 25000) penalties.push(-25)  // X Premium max limit
  if (hasLink) penalties.push(-15)
  if (emojiCount > 5) penalties.push(-20)
  if (hashtagCount > 3) penalties.push(-15)
  if (!hasQuestion && !hasNewlines) penalties.push(-10)

  // Final Score
  let finalScore = (baseScore + penalties.reduce((a, b) => a + b, 0))
    * profileBoost * contentBonus * viralBonus * authorDiversityPenalty * timingBonus
  finalScore = Math.max(0, Math.min(100, finalScore))

  // Engagement Prediction
  const baseEngagement = (finalScore / 100)
  const engagement_prediction = {
    favorite: 0.02 + baseEngagement * 0.08,
    reply: 0.005 + (hasQuestion ? 0.025 : 0.005) + baseEngagement * 0.04,
    repost: 0.003 + baseEngagement * 0.03,
    quote: 0.002 + baseEngagement * 0.025,
    follow: baseEngagement * 0.025 + (profile?.verified ? 0.01 : 0),
    click: 0.01 + baseEngagement * 0.05,
    profile_click: 0.005 + baseEngagement * 0.02,
    video_view: content.includes("video") ? 0.05 + baseEngagement * 0.15 : 0,
    photo_expand: 0.01 + baseEngagement * 0.04,
    share: 0.002 + baseEngagement * 0.015,
    dwell: isLongForm ? 0.1 + baseEngagement * 0.2 : 0.05 + baseEngagement * 0.1,
    not_interested: 0.05 - baseEngagement * 0.03,
    block: Math.max(0, 0.005 - baseEngagement * 0.003),
    mute: Math.max(0, 0.01 - baseEngagement * 0.008),
    report: Math.max(0, 0.001 - baseEngagement * 0.0005),
  }

  // Phoenix Insights
  const phoenix_insights = {
    candidate_isolation_ready: true,
    golden_hour_status: "Yeni post - Golden Hour başlıyor",
    author_diversity_status: profile?.recent_post_count && profile.recent_post_count > 2
      ? "⚠️ Spam riski" : "✓ Optimal",
    tweetcred_status: !profile ? "Yeni hesap (-128)" : "✓ TweetCred pozitif",
    engagement_debt_status: !profile || profile.total_posts < ENGAGEMENT_DEBT_POSTS
      ? `İlk 100 post dönemi (${profile?.total_posts || 0}/100)` : "✓ Engagement Debt tamamlandı",
  }

  // Strengths & Weaknesses
  const strengths: string[] = []
  const weaknesses: string[] = []
  const suggestions: string[] = []

  if (hasQuestion) strengths.push("Soru içeriyor (reply teşviki - +1.5 ağırlık)")
  if (!hasLink) strengths.push("Dış link yok (daha iyi reach)")
  if (emojiCount >= 1 && emojiCount <= 3) strengths.push("Emoji kullanımı optimal")
  if (hasNewlines) strengths.push("Okunabilir format (dwell time artışı)")
  if (viralBonus > 1.0) strengths.push("Viral potansiyel içerik")
  if (isLongForm) strengths.push("Dwell time potansiyeli yüksek")

  if (hasLink) weaknesses.push("Dış link içeriyor (reach düşebilir)")
  if (emojiCount > 5) weaknesses.push("Çok emoji (spam sinyali)")
  if (hashtagCount > 3) weaknesses.push("Çok hashtag (spam sinyali)")
  if (length > 25000) weaknesses.push("Maksimum limit aşıldı (25.000)")
  if (!hasQuestion && !hasNewlines) weaknesses.push("Etkileşim teşvik etmiyor")

  if (finalScore < 50) suggestions.push("Daha etkileşimci olun")
  if (!hasQuestion) suggestions.push("Soru ekleyin (reply en yüksek ağırlık)")
  if (emojiCount === 0) suggestions.push("1-2 emoji ekleyin")

  return {
    score: Math.round(finalScore),
    rawScore: finalScore,
    maxScore: 100 * profileBoost * contentBonus * viralBonus * timingBonus,
    distributionRate,
    strengths,
    weaknesses,
    suggestions,
    warnings: warnings.length > 0 ? warnings : undefined,
    breakdown: {
      baseScore,
      profileBoost,
      contentBonus,
      timingBonus,
      viralBonus,
      authorDiversityPenalty,
      penalties
    },
    engagement_prediction,
    phoenix_insights
  }
}
