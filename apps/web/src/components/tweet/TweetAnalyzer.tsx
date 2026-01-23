"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { api } from "@/lib/api"
import { Search, Loader2, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { cn } from "@/lib/utils"

export function TweetAnalyzer() {
  const { toast } = useToast()

  const [content, setContent] = useState("")
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleAnalyze = async () => {
    if (!content.trim()) {
      toast({
        variant: "destructive",
        title: "Tweet gereklidir",
        description: "Lütfen analiz edilecek tweet'i girin",
      })
      return
    }

    setLoading(true)
    setAnalysis(null)

    try {
      const result = await api.analyzeTweet(content.trim())
      setAnalysis(result)

      toast({
        title: "Analiz tamamlandı",
        description: `Skor: ${result.score}/100`,
      })
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Analiz başarısız",
        description: error.message || "Bir hata oluştu",
      })
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 70) return "bg-green-500 text-green-950"
    if (score >= 50) return "bg-yellow-500 text-yellow-950"
    return "bg-red-500 text-red-950"
  }

  const getScoreIcon = (score: number) => {
    if (score >= 70) return TrendingUp
    if (score >= 50) return Minus
    return TrendingDown
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Tweet Analizi
          </CardTitle>
          <CardDescription>
            X'in algoritmasına göre tweet'inizi analiz edin
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Tweet</label>
            <Textarea
              placeholder="Analiz edilecek tweet'i buraya yapıştırın..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={12}
              className="resize-none"
            />
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{content.length} karakter</span>
              {content.length > 280 && (
                <span className="text-red-500">
                  Standard limit aşıldı (280)
                </span>
              )}
            </div>
          </div>

          <Button
            onClick={handleAnalyze}
            disabled={loading || !content.trim()}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Analiz ediliyor...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Analiz Et
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader>
          <CardTitle>Analiz Sonucu</CardTitle>
          <CardDescription>
            {analysis ? `Skor: ${analysis.score}/100` : "Analiz bekleniyor..."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {analysis ? (
            <div className="space-y-6">
              {/* Score Badge */}
              <div className={cn(
                "flex items-center justify-center p-6 rounded-lg",
                getScoreColor(analysis.score)
              )}>
                {(() => {
                  const Icon = getScoreIcon(analysis.score)
                  return <Icon className="w-8 h-8 mr-2" />
                })()}
                <div className="text-center">
                  <div className="text-4xl font-bold">{analysis.score}</div>
                  <div className="text-sm opacity-80">/ 100</div>
                </div>
              </div>

              {/* Strengths */}
              {analysis.strengths && analysis.strengths.length > 0 && (
                <div className="space-y-2">
                  <h3 className="font-semibold text-green-600 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    Güçlü Yönler
                  </h3>
                  <ul className="space-y-1">
                    {analysis.strengths.map((s: string, i: number) => (
                      <li key={i} className="text-sm bg-green-50 p-2 rounded text-green-800">
                        ✓ {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Weaknesses */}
              {analysis.weaknesses && analysis.weaknesses.length > 0 && (
                <div className="space-y-2">
                  <h3 className="font-semibold text-red-600 flex items-center gap-2">
                    <TrendingDown className="w-4 h-4" />
                    Zayıf Yönler
                  </h3>
                  <ul className="space-y-1">
                    {analysis.weaknesses.map((w: string, i: number) => (
                      <li key={i} className="text-sm bg-red-50 p-2 rounded text-red-800">
                        ✗ {w}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Suggestions */}
              {analysis.suggestions && analysis.suggestions.length > 0 && (
                <div className="space-y-2">
                  <h3 className="font-semibold text-blue-600">💡 Öneriler</h3>
                  <ul className="space-y-1">
                    {analysis.suggestions.map((s: string, i: number) => (
                      <li key={i} className="text-sm bg-blue-50 p-2 rounded text-blue-800">
                        • {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Engagement Prediction */}
              {analysis.engagement_prediction && (
                <div className="space-y-2 pt-4 border-t">
                  <h3 className="font-semibold">Etkileşim Tahmini</h3>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 bg-muted rounded text-center">
                      <div className="text-xs text-muted-foreground">Like</div>
                      <div className="font-semibold">
                        {(analysis.engagement_prediction.favorite * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-2 bg-muted rounded text-center">
                      <div className="text-xs text-muted-foreground">Reply</div>
                      <div className="font-semibold">
                        {(analysis.engagement_prediction.reply * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-2 bg-muted rounded text-center">
                      <div className="text-xs text-muted-foreground">Retweet</div>
                      <div className="font-semibold">
                        {(analysis.engagement_prediction.repost * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-2 bg-muted rounded text-center">
                      <div className="text-xs text-muted-foreground">Follow</div>
                      <div className="font-semibold">
                        {(analysis.engagement_prediction.follow_author * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Search className="w-12 h-12 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground">
                Analiz sonuçları burada görünecek
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
