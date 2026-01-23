"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { Palette } from "lucide-react"

export function StyleAnalyzer() {
  const { toast } = useToast()

  const [tweetsInput, setTweetsInput] = useState("")
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleAnalyze = async () => {
    const lines = tweetsInput.trim().split("\n").filter((l) => l.trim())

    if (lines.length < 5) {
      toast({
        variant: "destructive",
        title: "En az 5 tweet gereklidir",
        description: "Lütfen daha fazla tweet girin",
      })
      return
    }

    setLoading(true)

    try {
      const tweets = lines.map((line) => {
        const parts = line.split("|")
        return {
          text: parts[0].trim(),
          likes: parts[1] ? parseInt(parts[1].trim()) : 0,
          retweets: parts[2] ? parseInt(parts[2].trim()) : 0,
          replies: parts[3] ? parseInt(parts[3].trim()) : 0,
          impressions: parts[4] ? parseInt(parts[4].trim()) : 100,
        }
      })

      const response = await fetch("/api/style/analyze-style", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tweets }),
      })

      if (!response.ok) {
        throw new Error("Analysis failed")
      }

      const data = await response.json()
      setAnalysis(data)

      toast({
        title: "Stil analizi tamamlandı!",
        description: `${lines.length} tweet analiz edildi`,
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

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="w-5 h-5" />
            Stil Analizi
          </CardTitle>
          <CardDescription>
            Tweetlerinizi analiz ederek yazım stilinizi öğrenin
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Tweetlerinizi Yapıştırın
            </label>
            <div className="text-xs text-muted-foreground mb-2">
              Format: tweet metni | likes | retweets | replies | impressions
            </div>
            <Textarea
              placeholder={`Harika bir gün! 🌞 | 150 | 30 | 15 | 2000
İkinci tweet buraya... | 200 | 50 | 25 | 3500`}
              value={tweetsInput}
              onChange={(e) => setTweetsInput(e.target.value)}
              rows={12}
              className="resize-none font-mono text-sm"
            />
          </div>

          <div className="text-xs text-muted-foreground">
            {tweetsInput.trim().split("\n").filter((l) => l.trim()).length} tweet girildi
            (min 5)
          </div>

          <Button
            onClick={handleAnalyze}
            disabled={loading}
            className="w-full"
            size="lg"
          >
            {loading ? "Analiz ediliyor..." : "Analiz Et"}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader>
          <CardTitle>Analiz Sonuçları</CardTitle>
          <CardDescription>
            {analysis ? `Tespit edilen stil: ${analysis.tone}` : "Sonuçlar burada görünecek"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {analysis ? (
            <div className="space-y-6">
              {/* Metrics */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-3 bg-muted rounded-lg text-center">
                  <div className="text-2xl font-bold">
                    {Math.round(analysis.avg_length)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Ort. Uzunluk
                  </div>
                </div>

                <div className="p-3 bg-muted rounded-lg text-center">
                  <div className="text-2xl font-bold">
                    {analysis.emoji_frequency.toFixed(1)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Emoji / Tweet
                  </div>
                </div>

                <div className="p-3 bg-muted rounded-lg text-center">
                  <div className="text-2xl font-bold">
                    {(analysis.question_frequency * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Soru Oranı
                  </div>
                </div>
              </div>

              {/* Common Emojis */}
              {analysis.common_emojis && analysis.common_emojis.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium mb-2">Sık Kullanılan Emojiler</h3>
                  <div className="flex gap-1 flex-wrap">
                    {analysis.common_emojis.map((emoji: string, i: number) => (
                      <span key={i} className="text-2xl">{emoji}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Common Words */}
              {analysis.common_words && analysis.common_words.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium mb-2">Sık Kullanılan Kelimeler</h3>
                  <div className="flex flex-wrap gap-2">
                    {analysis.common_words.slice(0, 10).map((word: string, i: number) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-primary/10 text-primary rounded-full text-xs"
                      >
                        {word}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Style Prompt */}
              {analysis.style_prompt && (
                <div>
                  <h3 className="text-sm font-medium mb-2">AI Stil Özeti</h3>
                  <p className="text-sm bg-muted p-3 rounded-lg">
                    {analysis.style_prompt}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Palette className="w-12 h-12 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground">
                Stil analizi sonuçları burada görünecek
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
