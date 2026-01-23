const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl
    // Load token from localStorage on client side
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("supabase_token")
    }
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== "undefined") {
      localStorage.setItem("supabase_token", token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== "undefined") {
      localStorage.removeItem("supabase_token")
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    }

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.message || "API request failed")
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
    return this.request<{ content: string; analysis: any }>("/api/v1/tweets/generate", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async analyzeTweet(tweet: string) {
    return this.request<any>("/api/v1/tweets/analyze", {
      method: "POST",
      body: JSON.stringify({ content: tweet }),
    })
  }

  async optimizeTweet(tweet: string) {
    return this.request<{ content: string; analysis: any }>("/api/v1/tweets/optimize", {
      method: "POST",
      body: JSON.stringify({ content: tweet }),
    })
  }

  async rewriteTweet(tweet: string, style: string) {
    return this.request<{ content: string; analysis: any }>("/api/v1/tweets/rewrite", {
      method: "POST",
      body: JSON.stringify({ content: tweet, style }),
    })
  }

  async getTweets() {
    return this.request<any[]>("/api/v1/tweets")
  }

  async getTweet(id: string) {
    return this.request<any>(`/api/v1/tweets/${id}`)
  }

  // Threads
  async generateThread(data: {
    topic: string
    tweet_count?: number
    style?: string
    language?: string
  }) {
    return this.request<{ tweets: string[] }>("/api/v1/threads/generate", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  // Scheduling
  async scheduleTweet(data: {
    content: string
    scheduled_for: string
    analysis?: any
  }) {
    return this.request<{ id: string }>("/api/v1/scheduling/schedule", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async getScheduledTweets() {
    return this.request<any[]>("/api/v1/scheduling/upcoming")
  }

  async deleteScheduledTweet(id: string) {
    return this.request<void>(`/api/v1/scheduling/${id}`, {
      method: "DELETE",
    })
  }

  // A/B Testing
  async createAbCampaign(data: {
    name: string
    variants: string[]
  }) {
    return this.request<{ id: string }>("/api/v1/ab/campaigns", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async getAbCampaigns() {
    return this.request<any[]>("/api/v1/ab/campaigns")
  }

  async getAbResults(id: string) {
    return this.request<any>(`/api/v1/ab/campaigns/${id}/results`)
  }

  async setAbWinner(campaignId: string, variantId: string) {
    return this.request<void>(`/api/v1/ab/campaigns/${campaignId}/winner`, {
      method: "POST",
      body: JSON.stringify({ variant_id: variantId }),
    })
  }

  // Profile
  async getProfile() {
    return this.request<any>("/api/v1/profiles/me")
  }

  async analyzeStyle(tweets: Array<{ text: string; likes?: number }>) {
    return this.request<any>("/api/v1/profiles/analyze-style", {
      method: "POST",
      body: JSON.stringify({ tweets }),
    })
  }

  async getTweetCred() {
    return this.request<any>("/api/v1/profiles/tweetcred")
  }

  async getMonetization() {
    return this.request<any>("/api/v1/profiles/monetization")
  }

  // Analytics
  async getAnalytics() {
    return this.request<any>("/api/v1/analytics/overview")
  }

  async getPerformance() {
    return this.request<any[]>("/api/v1/analytics/performance")
  }
}

export const api = new ApiClient()
