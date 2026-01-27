// API Client - Next.js API Routes
// Bu dosya artık backend yerine Next.js API route'larını kullanıyor

const API_BASE = "/api"

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.error || "API request failed")
    }

    return response.json()
  }

  // Tweets
  async generateTweet(data: {
    topic: string
    style?: string
    tone?: string
    length?: string
    language?: string
    include_cta?: boolean
    include_emoji?: boolean
    custom_instructions?: string
  }) {
    return this.request<{ content: string; analysis: any }>("/tweets/generate", {
      method: "POST",
      body: JSON.stringify({
        topic: data.topic,
        style: data.style,
        tone: data.tone,
        length: data.length,
        language: data.language,
        include_cta: data.include_cta,
        include_emoji: data.include_emoji,
        custom_instructions: data.custom_instructions,
      }),
    })
  }

  async analyzeTweet(tweet: string) {
    return this.request<{ analysis: any }>("/tweets/analyze", {
      method: "POST",
      body: JSON.stringify({ content: tweet }),
    })
  }

  async optimizeTweet(tweet: string) {
    // Şimdilik analyze ile aynı, sonra optimize endpoint'i eklenir
    return this.analyzeTweet(tweet)
  }

  async rewriteTweet(tweet: string, style: string) {
    // Mock - sonra gerçek implementasyon
    return this.analyzeTweet(tweet)
  }

  async getTweets() {
    const result = await this.request<{ tweets: any[] }>("/tweets")
    return result.tweets
  }

  async getTweet(id: string) {
    // Mock
    return null
  }

  async saveTweet(data: { content: string; analysis?: any; status?: string }) {
    return this.request<{ tweet: any }>("/tweets", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async updateTweet(id: string, data: any) {
    return this.request<{ tweet: any }>("/tweets", {
      method: "PATCH",
      body: JSON.stringify({ id, ...data }),
    })
  }

  async deleteTweet(id: string) {
    return this.request("/tweets", {
      method: "DELETE",
      body: JSON.stringify({ id }),
    })
  }

  // Threads
  async generateThread(data: {
    topic: string
    tweet_count?: number
    style?: string
    language?: string
  }) {
    return this.request<{ thread: Array<{ content: string; analysis: any }> }>("/threads/generate", {
      method: "POST",
      body: JSON.stringify({
        topic: data.topic,
        tweetCount: data.tweet_count,
        style: data.style,
      }),
    })
  }

  // Scheduling
  async scheduleTweet(data: {
    content: string
    scheduled_for: string
    analysis?: any
  }) {
    return this.saveTweet({
      ...data,
      status: "scheduled"
    })
  }

  async getScheduledTweets() {
    const tweets = await this.getTweets()
    return tweets.filter((t: any) => t.status === "scheduled")
  }

  async deleteScheduledTweet(id: string) {
    return this.deleteTweet(id)
  }

  // A/B Testing
  async createAbCampaign(data: {
    name: string
    variants: string[]
  }) {
    // Mock
    return { id: crypto.randomUUID() }
  }

  async getAbCampaigns() {
    // Mock
    return []
  }

  async getAbResults(id: string) {
    // Mock
    return null
  }

  async setAbWinner(campaignId: string, variantId: string) {
    // Mock
    return
  }

  // Profile
  async getProfile() {
    // Session'dan alınıyor
    return null
  }

  async analyzeStyle(tweets: Array<{ text: string; likes?: number }>) {
    // Mock
    return { style: "casual", tone: "friendly" }
  }

  async getTweetCred() {
    // Mock
    return { score: 50 }
  }

  async getMonetization() {
    // Mock
    return { potential: 0 }
  }

  // Analytics
  async getAnalytics() {
    // Mock
    return {}
  }

  async getPerformance() {
    // Mock
    return []
  }
}

export const api = new ApiClient()
