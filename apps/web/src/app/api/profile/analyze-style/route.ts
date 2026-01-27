import { NextRequest, NextResponse } from "next/server"

// Style Analysis API - Analyze tweets to extract user's writing style

interface Tweet {
  text: string
  likes?: number
  retweets?: number
  replies?: number
  views?: number
}

interface StyleAnalysis {
  avg_length: number
  avg_line_breaks: number
  emoji_frequency: number  // emojis per tweet
  question_frequency: number  // tweets with questions ratio
  hashtag_frequency: number
  mention_frequency: number
  link_frequency: number
  common_words: string[]
  common_emojis: string[]
  tone: string  // professional, casual, provocative, educational, neutral
  topics: string[]
  avg_engagement_rate: number
  best_performing_patterns: string[]
  recommendations: string[]
  style_prompt_addition: string  // AI prompt için eklenecek stil açıklaması
}

const EMOJI_PATTERN = /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu

// Tone detection keywords
const TONE_KEYWORDS = {
  provocative: ['tartışmalı', 'yanlış', 'hata', 'aslında', 'unpopular', 'controversial', 'wrong', 'mistake', 'sanmıyorum', 'katılmıyorum'],
  educational: ['öğrendim', 'ipucu', 'rehber', 'nasıl', 'adım', 'learned', 'tips', 'guide', 'how to', 'step', 'bilmeniz gereken'],
  casual: ['haha', 'lol', 'sjsj', 'random', 'wtf', 'omg', '😂', '😭', 'kanka', 'arkadaşlar'],
  professional: ['analiz', 'strateji', 'veri', 'rapor', 'analysis', 'strategy', 'data', 'report', 'araştırma', 'sonuç'],
}

const TOPIC_KEYWORDS = {
  teknoloji: ['yapay zeka', 'ai', 'teknoloji', 'yazılım', 'kod', 'tech', 'software', 'developer'],
  iş: ['startup', 'iş', 'kariyer', 'girişim', 'iş dünyası', 'career', 'business', 'startup'],
  finans: ['yatırım', 'borsa', 'kripto', 'para', 'finans', 'investment', 'stock', 'crypto'],
  yaşam: ['hayat', 'günlük', 'yaşam', 'deneyim', 'life', 'daily', 'experience'],
  eğitim: ['öğren', 'eğitim', 'kurs', 'kitap', 'learn', 'education', 'course', 'book'],
}

function calculateEngagementRate(tweet: Tweet): number {
  const views = tweet.views || 0
  if (views === 0) return 0

  const likes = tweet.likes || 0
  const retweets = tweet.retweets || 0
  const replies = tweet.replies || 0

  // Weighted engagement formula
  return (likes + retweets * 2 + replies * 1.5) / views
}

function detectTone(texts: string[]): string {
  const combinedText = texts.join(" ").toLowerCase()

  const scores: Record<string, number> = {}
  for (const [tone, keywords] of Object.entries(TONE_KEYWORDS)) {
    scores[tone] = keywords.reduce((sum, word) => {
      return sum + (combinedText.includes(word) ? 1 : 0)
    }, 0)
  }

  const maxScore = Math.max(...Object.values(scores))
  if (maxScore === 0) return "neutral"

  return Object.entries(scores).find(([, score]) => score === maxScore)?.[0] || "neutral"
}

function detectTopics(texts: string[]): string[] {
  const combinedText = texts.join(" ").toLowerCase()
  const detected: string[] = []

  for (const [topic, keywords] of Object.entries(TOPIC_KEYWORDS)) {
    if (keywords.some(keyword => combinedText.includes(keyword))) {
      detected.push(topic.charAt(0).toUpperCase() + topic.slice(1))
    }
  }

  return detected.length > 0 ? detected : ["Genel"]
}

export async function POST(req: NextRequest) {
  try {
    const { tweets } = await req.json()

    if (!tweets || !Array.isArray(tweets) || tweets.length === 0) {
      return NextResponse.json({ error: "Tweets array is required" }, { status: 400 })
    }

    const analysis = analyzeStyle(tweets)
    return NextResponse.json(analysis)
  } catch (error: any) {
    console.error("Style analysis error:", error)
    return NextResponse.json(
      { error: error.message || "Analysis failed" },
      { status: 500 }
    )
  }
}

function analyzeStyle(tweets: Tweet[]): StyleAnalysis {
  const n = tweets.length

  // Basic stats
  let totalLength = 0
  let totalLineBreaks = 0
  let totalEmojis = 0
  let questionCount = 0
  let hashtagCount = 0
  let mentionCount = 0
  let linkCount = 0

  const allEmojis: string[] = []
  const allWords: string[] = []
  const engagementRates: number[] = []

  // Turkish stop words
  const stopwords = new Set([
    'için', 'olan', 'gibi', 'daha', 'çok', 'kadar', 'nasıl', 'neden', 'ile', 'bu', 'şu',
    'her', 'ama', 'fakat', 'yoksa', 've', 'veya', 'ya', 'ise', 'ki', 'de', 'da',
    'that', 'this', 'with', 'from', 'have', 'been', 'will', 'your', 'they', 'what', 'when', 'there'
  ])

  for (const tweet of tweets) {
    const text = tweet.text || ""

    // Length
    totalLength += text.length

    // Line breaks
    totalLineBreaks += (text.match(/\n/g) || []).length

    // Emojis
    const emojis = text.match(EMOJI_PATTERN) || []
    totalEmojis += emojis.length
    allEmojis.push(...emojis)

    // Questions
    if (text.includes('?')) questionCount++

    // Hashtags
    hashtagCount += (text.match(/#/g) || []).length

    // Mentions
    mentionCount += (text.match(/@/g) || []).length

    // Links
    if (text.includes('http')) linkCount++

    // Words (4+ characters)
    const words = text.toLowerCase().match(/\b[a-zA-ZğüşıöçĞÜŞİÖÇ]{4,}\b/g) || []
    allWords.push(...words.filter(w => !stopwords.has(w)))

    // Engagement
    const rate = calculateEngagementRate(tweet)
    if (rate > 0) engagementRates.push(rate)
  }

  // Calculate averages
  const avgLength = totalLength / n
  const avgLineBreaks = totalLineBreaks / n
  const emojiFrequency = totalEmojis / n
  const questionFrequency = questionCount / n
  const hashtagFrequency = hashtagCount / n
  const mentionFrequency = mentionCount / n
  const linkFrequency = linkCount / n

  // Common emojis
  const emojiCounts: Record<string, number> = {}
  for (const emoji of allEmojis) {
    emojiCounts[emoji] = (emojiCounts[emoji] || 0) + 1
  }
  const commonEmojis = Object.entries(emojiCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([emoji]) => emoji)

  // Common words
  const wordCounts: Record<string, number> = {}
  for (const word of allWords) {
    wordCounts[word] = (wordCounts[word] || 0) + 1
  }
  const commonWords = Object.entries(wordCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([word]) => word)

  // Tone
  const texts = tweets.map(t => t.text || "")
  const tone = detectTone(texts)

  // Topics
  const topics = detectTopics(texts)

  // Avg engagement
  const avgEngagementRate = engagementRates.length > 0
    ? engagementRates.reduce((a, b) => a + b, 0) / engagementRates.length
    : 0

  // Best performing patterns
  const bestPerformingPatterns: string[] = []

  if (questionFrequency > 0.5) {
    bestPerformingPatterns.push("Soru sorma (daha yüksek engagement)")
  }
  if (avgLength > 200) {
    bestPerformingPatterns.push("Uzun içerik (dwell time artışı)")
  }
  if (emojiFrequency > 1) {
    bestPerformingPatterns.push("Emoji kullanımı")
  }

  // Recommendations
  const recommendations: string[] = []

  if (questionFrequency < 0.3) {
    recommendations.push("Daha fazla soru ekleyin (reply almak için)")
  }
  if (emojiFrequency === 0) {
    recommendations.push("Emoji kullanmayı deneyin")
  }
  if (avgLength < 100) {
    recommendations.push("Daha uzun, detaylı içerik deneyin")
  }
  if (linkFrequency > 0.5) {
    recommendations.push("Dış link kullanımını azaltın (reach için)")
  }

  // Style prompt for AI
  const stylePromptAddition = generateStylePrompt({
    avgLength,
    emojiFrequency,
    questionFrequency,
    tone,
    commonEmojis,
    commonWords,
  })

  return {
    avg_length: Math.round(avgLength),
    avg_line_breaks: Math.round(avgLineBreaks * 10) / 10,
    emoji_frequency: Math.round(emojiFrequency * 10) / 10,
    question_frequency: Math.round(questionFrequency * 100) / 100,
    hashtag_frequency: Math.round(hashtagFrequency * 10) / 10,
    mention_frequency: Math.round(mentionFrequency * 10) / 10,
    link_frequency: Math.round(linkFrequency * 10) / 10,
    common_words: commonWords,
    common_emojis: commonEmojis,
    tone,
    topics,
    avg_engagement_rate: Math.round(avgEngagementRate * 1000) / 1000,
    best_performing_patterns: bestPerformingPatterns,
    recommendations,
    style_prompt_addition: stylePromptAddition,
  }
}

function generateStylePrompt(data: {
  avgLength: number
  emojiFrequency: number
  questionFrequency: number
  tone: string
  commonEmojis: string[]
  commonWords: string[]
}): string {
  const parts: string[] = []

  parts.push("\nKULLANICI STİL BİLGİLERİ:")

  // Length preference
  if (data.avgLength < 150) {
    parts.push("- Kısa ve öz tweetler tercih ediyor")
  } else if (data.avgLength < 300) {
    parts.push("- Orta uzunlukta tweetler yazıyor")
  } else {
    parts.push("- Uzun, detaylı threadler yazıyor")
  }

  // Emoji usage
  if (data.emojiFrequency > 1) {
    parts.push(`- Sık emoji kullanıyor: ${data.commonEmojis.slice(0, 3).join(" ")}`)
  } else if (data.emojiFrequency > 0) {
    parts.push("- Ara sıra emoji kullanıyor")
  } else {
    parts.push("- Emoji kullanmıyor")
  }

  // Question usage
  if (data.questionFrequency > 0.5) {
    parts.push("- Sık soru soruyor (etkileşimci)")
  }

  // Tone
  if (data.tone !== "neutral") {
    const toneMap: Record<string, string> = {
      professional: "Profesyonel",
      casual: "Samimi",
      provocative: "Provokatif",
      educational: "Eğitici",
    }
    parts.push(`- Ton: ${toneMap[data.tone] || data.tone}`)
  }

  // Common topics
  if (data.commonWords.length > 0) {
    parts.push(`- Sık kullandığı kelimeler: ${data.commonWords.slice(0, 5).join(", ")}`)
  }

  return parts.join("\n")
}
