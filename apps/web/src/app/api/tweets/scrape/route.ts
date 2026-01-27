import { NextRequest, NextResponse } from "next/server"

// Tweet Scraper API
// Nitter/ntscraper alternative - public endpoints

interface ScrapeResult {
  username: string
  tweets: Array<{
    text: string
    likes: number
    retweets: number
    replies: number
    views: number
    date: string
    url: string
  }>
  source: string
  error?: string
}

// Nitter instances (public)
const NITTER_INSTANCES = [
  "https://nitter.net",
  "https://nitter.poast.org",
  "https://nitter.privacydev.net",
  "https://nitter.1d4.us",
  "https://nitter.kavin.rocks",
]

async function scrapeFromNitter(username: string, count: number = 20): Promise<ScrapeResult> {
  // Try each Nitter instance
  for (const instance of NITTER_INSTANCES) {
    try {
      const url = `${instance}/${username}`
      const response = await fetch(url, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
      })

      if (!response.ok) continue

      const html = await response.text()

      // Parse HTML to extract tweets
      const tweets: ScrapeResult["tweets"] = []
      const tweetRegex = /<div class="tweet-content[^>]*>(.*?)<\/div>/gs
      const statsRegex = /<span class="tweet-stats[^>]*>(.*?)<\/span>/gs

      let match
      let index = 0
      while ((match = tweetRegex.exec(html)) !== null && index < count) {
        const content = match[1]
          .replace(/<[^>]*>/g, "")
          .replace(/&amp;/g, "&")
          .replace(/&lt;/g, "<")
          .replace(/&gt;/g, ">")
          .replace(/&quot;/g, '"')
          .trim()

        if (content.length > 10) {
          tweets.push({
            text: content,
            likes: 0,
            retweets: 0,
            replies: 0,
            views: 0,
            date: new Date().toISOString(),
            url: `${instance}/${username}`,
          })
          index++
        }
      }

      if (tweets.length > 0) {
        return {
          username,
          tweets,
          source: instance,
        }
      }
    } catch (e) {
      console.error(`${instance} failed:`, e)
      continue
    }
  }

  return {
    username,
    tweets: [],
    source: "none",
    error: "Nitter instances failed. Try providing tweets manually.",
  }
}

// Alternative: Use mock data for demo (when Nitter fails)
function generateMockTweets(username: string, count: number = 10): ScrapeResult {
  const mockTemplates = [
    "Teknoloji dünyasında çok şey değişiyor. Kimse geride kalmak istemiyor.",
    "Bugün öğrendiğim bir şey: Başarı tesadüf değil, tutarlı çabanın sonucu.",
    "Yapay zeka alanındaki gelişmeler inanılmaz. Sizce nereye gidiyoruz?",
    "Startup dünyasında 1 yıl = 10 yıl. Hız her şey.",
    "Kod yazarken müzik dinlemek üretkenliğimi artırıyor. Siz?",
  ]

  const tweets: ScrapeResult["tweets"] = []
  for (let i = 0; i < Math.min(count, mockTemplates.length); i++) {
    tweets.push({
      text: mockTemplates[i],
      likes: Math.floor(Math.random() * 500),
      retweets: Math.floor(Math.random() * 100),
      replies: Math.floor(Math.random() * 50),
      views: Math.floor(Math.random() * 5000),
      date: new Date(Date.now() - i * 86400000).toISOString(),
      url: `https://x.com/${username}`,
    })
  }

  return {
    username,
    tweets,
    source: "demo",
  }
}

export async function POST(req: NextRequest) {
  try {
    const { username, count = 20, useDemo = false } = await req.json()

    if (!username) {
      return NextResponse.json({ error: "Username is required" }, { status: 400 })
    }

    // Clean username (remove @ if present)
    const cleanUsername = username.replace(/^@/, "")

    let result: ScrapeResult

    if (useDemo) {
      result = generateMockTweets(cleanUsername, count)
    } else {
      // Try Nitter first
      result = await scrapeFromNitter(cleanUsername, count)

      // Fallback to demo if all instances fail
      if (result.tweets.length === 0) {
        result = generateMockTweets(cleanUsername, count)
        result.error = "Nitter failed, using demo data. Provide tweets manually for accurate analysis."
      }
    }

    return NextResponse.json(result)
  } catch (error: any) {
    console.error("Scrape error:", error)
    return NextResponse.json(
      { error: error.message || "Scraping failed" },
      { status: 500 }
    )
  }
}

// GET endpoint for quick demo
export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const username = searchParams.get("username") || "demo"

  const result = generateMockTweets(username, 10)
  return NextResponse.json(result)
}
