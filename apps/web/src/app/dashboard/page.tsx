import { createClient } from "@/lib/supabase/server"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import {
  FileText,
  TrendingUp,
  Clock,
  Zap,
  ArrowRight
} from "lucide-react"

export default async function DashboardPage() {
  const supabase = createClient()

  const { data: { user } } = await supabase.auth.getUser()

  // Get user profile
  const { data: profile } = await supabase
    .from("profiles")
    .select("*")
    .eq("id", user?.id)
    .single()

  // Get recent tweets
  const { data: tweets } = await supabase
    .from("tweets")
    .select("*")
    .eq("user_id", user?.id)
    .order("created_at", { ascending: false })
    .limit(5)

  // Get analytics
  const { data: allTweets } = await supabase
    .from("tweets")
    .select("*")
    .eq("user_id", user?.id)

  const totalTweets = allTweets?.length || 0
  const draftCount = allTweets?.filter((t: any) => t.status === "draft").length || 0
  const scheduledCount = allTweets?.filter((t: any) => t.status === "scheduled").length || 0

  // Calculate average score
  const scores = allTweets
    ?.map((t: any) => t.analysis?.score)
    .filter((s: any) => s !== undefined && s !== null) || []
  const avgScore = scores.length > 0
    ? Math.round(scores.reduce((a: number, b: number) => a + b, 0) / scores.length)
    : 0

  const followers = profile?.followers || 0

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Hoş geldiniz, {user?.user_metadata?.name || user?.email}
          </p>
        </div>
        <Link href="/dashboard/generate">
          <Button size="lg">
            <Zap className="w-4 h-4 mr-2" />
            Tweet Üret
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Toplam Tweet
            </CardTitle>
            <FileText className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTweets}</div>
            <p className="text-xs text-muted-foreground">
              {draftCount} taslak, {scheduledCount} planlanmış
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Ortalama Skor
            </CardTitle>
            <TrendingUp className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgScore}/100</div>
            <p className="text-xs text-muted-foreground">
              {avgScore >= 70 ? "Mükemmel" : avgScore >= 50 ? "İyi" : "Geliştirilmeli"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Takipçi
            </CardTitle>
            <svg className="w-4 h-4 text-muted-foreground" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{followers.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {followers >= 1000 ? "X hesabı bağlı" : "X hesabı bağla"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Planlanan
            </CardTitle>
            <Clock className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scheduledCount}</div>
            <p className="text-xs text-muted-foreground">
              Otomatik paylaşılacak
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle>AI Tweet Üret</CardTitle>
            <CardDescription>
              Claude AI ile viral potansiyelli tweetler üretin
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/dashboard/generate">
              <Button className="w-full">
                Üretmeye Başla
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle>Tweet Analizi</CardTitle>
            <CardDescription>
              X algoritmasına göre tweet'inizi analiz edin
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/dashboard/analyze">
              <Button className="w-full" variant="outline">
                Analiz Et
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle>A/B Test</CardTitle>
            <CardDescription>
              Farklı varyasyonları test edin
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/dashboard/ab-test">
              <Button className="w-full" variant="outline">
                Test Başlat
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Recent Tweets */}
      <Card>
        <CardHeader>
          <CardTitle>Son Tweetler</CardTitle>
          <CardDescription>
            Son ürettiğiniz veya kaydettiğiniz tweetler
          </CardDescription>
        </CardHeader>
        <CardContent>
          {tweets && tweets.length > 0 ? (
            <div className="space-y-4">
              {tweets.slice(0, 5).map((tweet: any) => (
                <div
                  key={tweet.id}
                  className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      tweet.status === "draft"
                        ? "bg-gray-100 text-gray-700"
                        : tweet.status === "scheduled"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-green-100 text-green-700"
                    }`}>
                      {tweet.status === "draft" ? "Taslak" :
                       tweet.status === "scheduled" ? "Planlandı" : "Paylaşıldı"}
                    </span>
                    {tweet.analysis?.score && (
                      <span className="text-sm font-medium">
                        Skor: {tweet.analysis.score}/100
                      </span>
                    )}
                  </div>
                  <p className="text-sm line-clamp-2">{tweet.content}</p>
                  <p className="text-xs text-muted-foreground mt-2">
                    {new Date(tweet.created_at).toLocaleDateString("tr-TR")}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              Henüz tweet üretmediniz.
              <Link href="/dashboard/generate" className="text-primary hover:underline ml-2">
                İlk tweet'i üret
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
