import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import { db } from "@/lib/db"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart3, TrendingUp, FileText, Star } from "lucide-react"

export default async function AnalyticsPage() {
  const session = await getServerSession(authOptions)
  const userId = session?.user?.id

  // Get all tweets
  const tweets = userId ? await db.getTweetsByUserId(userId, 1000) : []

  // Calculate stats
  const totalTweets = tweets?.length || 0
  const draftCount = tweets?.filter((t: any) => t.status === "draft").length || 0
  const scheduledCount = tweets?.filter((t: any) => t.status === "scheduled").length || 0
  const postedCount = tweets?.filter((t: any) => t.status === "posted").length || 0

  const scores = tweets
    ?.map((t: any) => t.analysis?.score)
    .filter((s: any) => s !== undefined && s !== null) || []

  const avgScore = scores.length > 0
    ? Math.round(scores.reduce((a: number, b: number) => a + b, 0) / scores.length)
    : 0

  const highPerformers = scores.filter((s: number) => s >= 70).length
  const lowPerformers = scores.filter((s: number) => s < 50).length

  // Score distribution
  const scoreRanges = {
    excellent: scores.filter((s: number) => s >= 80).length,
    good: scores.filter((s: number) => s >= 60 && s < 80).length,
    average: scores.filter((s: number) => s >= 40 && s < 60).length,
    poor: scores.filter((s: number) => s < 40).length,
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground">
          Tweet performansınızı ve istatistikleriniz
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Toplam Tweet</CardTitle>
            <FileText className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTweets}</div>
            <p className="text-xs text-muted-foreground">
              {draftCount} taslak, {postedCount} paylaşıldı
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Ortalama Skor</CardTitle>
            <BarChart3 className="w-4 h-4 text-muted-foreground" />
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
            <CardTitle className="text-sm font-medium">Yüksek Performans</CardTitle>
            <Star className="w-4 h-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{highPerformers}</div>
            <p className="text-xs text-muted-foreground">
              70+ skorlu tweet
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Planlanan</CardTitle>
            <TrendingUp className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scheduledCount}</div>
            <p className="text-xs text-muted-foreground">
              Otomatik paylaşılacak
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Score Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Skor Dağılımı</CardTitle>
          <CardDescription>
            Tweetlerinizin algoritma skorlarına göre dağılımı
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-24 text-sm">Mükemmel (80+)</div>
              <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full"
                  style={{
                    width: `${scores.length > 0 ? (scoreRanges.excellent / scores.length) * 100 : 0}%`
                  }}
                />
              </div>
              <div className="w-12 text-sm text-right">{scoreRanges.excellent}</div>
            </div>

            <div className="flex items-center gap-4">
              <div className="w-24 text-sm">İyi (60-79)</div>
              <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full"
                  style={{
                    width: `${scores.length > 0 ? (scoreRanges.good / scores.length) * 100 : 0}%`
                  }}
                />
              </div>
              <div className="w-12 text-sm text-right">{scoreRanges.good}</div>
            </div>

            <div className="flex items-center gap-4">
              <div className="w-24 text-sm">Orta (40-59)</div>
              <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-yellow-500 rounded-full"
                  style={{
                    width: `${scores.length > 0 ? (scoreRanges.average / scores.length) * 100 : 0}%`
                  }}
                />
              </div>
              <div className="w-12 text-sm text-right">{scoreRanges.average}</div>
            </div>

            <div className="flex items-center gap-4">
              <div className="w-24 text-sm">Düşük (&lt;40)</div>
              <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 rounded-full"
                  style={{
                    width: `${scores.length > 0 ? (scoreRanges.poor / scores.length) * 100 : 0}%`
                  }}
                />
              </div>
              <div className="w-12 text-sm text-right">{scoreRanges.poor}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top Performing Tweets */}
      <Card>
        <CardHeader>
          <CardTitle>En İyi Tweetler</CardTitle>
          <CardDescription>
            En yüksek algoritma skoruna sahip tweetleriniz
          </CardDescription>
        </CardHeader>
        <CardContent>
          {tweets && tweets.length > 0 ? (
            <div className="space-y-3">
              {tweets
                .filter((t: any) => t.analysis?.score >= 60)
                .sort((a: any, b: any) => b.analysis.score - a.analysis.score)
                .slice(0, 5)
                .map((tweet: any) => (
                  <div
                    key={tweet.id}
                    className="p-4 border rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-green-600">
                        Skor: {tweet.analysis.score}/100
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(tweet.created_at).toLocaleDateString("tr-TR")}
                      </span>
                    </div>
                    <p className="text-sm line-clamp-2">{tweet.content}</p>
                  </div>
                ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              Henüz yeterli veri yok
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
