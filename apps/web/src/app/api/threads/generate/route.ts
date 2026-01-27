import { NextRequest, NextResponse } from "next/server"

// Thread Generation with AI
async function generateThreadWithAI(
  topic: string,
  tweetCount: number,
  style: string,
  language: string = "tr"
): Promise<{ tweets: string[]; total_characters: number }> {
  const apiKey = process.env.ANTHROPIC_API_KEY

  if (!apiKey) {
    throw new Error("Anthropic API key not configured")
  }

  const styleGuide: Record<string, string> = {
    educational: "Öğretici, bilgilendirici, adım adım açıklama",
    storytelling: "Hikaye anlatımı, kişisel deneyim, akıcı",
    provocative: "Tartışmalı, düşündürücü, farklı bakış açısı",
  }

  const systemPrompt = `Sen X (Twitter) için viral thread oluşturma uzmanısın.

KURALLAR:
- Her tweet maksimum 280 karakter (Premium: 25.000)
- Thread formatı: "🧵" başta, her tweet "1/", "2/", "3/" ile başlar
- İlk tweet (hook): Dikkat çekici, merak uyandırıcı
- Son tweet: CTA ile bitir
- Emoji kullanımı: 1-3 per tweet
- Hashtag: 0-2 per thread (son tweette)
- Soru sorarak etkileşim al
- Dış linklerden kaçın

STİL: ${styleGuide[style] || style}

SADECE thread'i JSON formatında ver:
{
  "tweets": ["tweet1", "tweet2", ...]
}`

  const userPrompt = `Konu: ${topic}
Tweet Sayısı: ${tweetCount}
Dil: ${language === "tr" ? "Türkçe" : "English"}
Stil: ${style}

GÖREV:
Bu konuda viral bir thread oluştur. ${tweetCount} tweet olmalı.
- Tweet 1: Hook (dikkat çekici giriş)
- Tweet 2-${tweetCount - 1}: İçerik
- Tweet ${tweetCount}: CTA ile bitir

Thread içeriği:`

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: tweetCount * 500,
      system: systemPrompt,
      messages: [{ role: "user", content: userPrompt }],
      temperature: 0.9,
    }),
  })

  if (!response.ok) {
    const error = await response.text()
    console.error("Anthropic API error:", error)
    throw new Error("AI generation failed")
  }

  const data = await response.json()
  const content = data.content?.[0]?.text || ""

  // Parse JSON response
  let tweets: string[] = []

  try {
    // Try to parse as JSON
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0])
      tweets = parsed.tweets || []
    }
  } catch {
    // Fallback: split by newlines
    tweets = content
      .split("\n\n")
      .filter((t: string) => t.trim().length > 10)
  }

  // Add thread formatting if not present
  tweets = tweets.map((tweet, i) => {
    if (!tweet.includes(`${i + 1}/`)) {
      return `${i + 1}/ ${tweet}`
    }
    return tweet
  })

  return {
    tweets: tweets.slice(0, tweetCount),
    total_characters: tweets.reduce((sum, t) => sum + t.length, 0),
  }
}

export async function POST(req: NextRequest) {
  try {
    const { topic, tweet_count = 5, style = "educational", language = "tr" } = await req.json()

    if (!topic) {
      return NextResponse.json({ error: "Topic is required" }, { status: 400 })
    }

    // Generate thread with AI
    const result = await generateThreadWithAI(topic, tweet_count, style, language)

    return NextResponse.json({
      tweets: result.tweets,
      total_characters: result.total_characters,
    })
  } catch (error: any) {
    console.error("Thread generation error:", error)
    return NextResponse.json(
      { error: error.message || "Thread generation failed" },
      { status: 500 }
    )
  }
}
