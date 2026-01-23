"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { useToast } from "@/hooks/use-toast"
import { api } from "@/lib/api"
import { Loader2, MessageSquare, Copy } from "lucide-react"
import { cn } from "@/lib/utils"

const THREAD_STYLES = [
  { value: "educational", label: "🎓 Eğitici" },
  { value: "storytelling", label: "📖 Hikaye" },
  { value: "provocative", label: "🔥 Provokatif" },
]

export function ThreadGenerator() {
  const { toast } = useToast()

  const [topic, setTopic] = useState("")
  const [tweetCount, setTweetCount] = useState(7)
  const [style, setStyle] = useState("educational")
  const [language, setLanguage] = useState("tr")

  const [threads, setThreads] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  const handleGenerate = async () => {
    if (!topic.trim()) {
      toast({
        variant: "destructive",
        title: "Konu gereklidir",
        description: "Lütfen bir konu girin",
      })
      return
    }

    setLoading(true)
    setThreads([])

    try {
      const params = new URLSearchParams({
        topic: topic.trim(),
        tweet_count: tweetCount.toString(),
        style,
        language,
      })

      const response = await fetch(`/api/threads/generate?${params}`, {
        method: "POST",
      })

      if (!response.ok) {
        throw new Error("Generation failed")
      }

      const data = await response.json()
      setThreads(data.tweets)

      toast({
        title: "Thread oluşturuldu!",
        description: `${data.tweets.length} tweet, ${data.total_characters} karakter`,
      })
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Oluşturma başarısız",
        description: error.message || "Bir hata oluştu",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCopyAll = () => {
    const fullThread = threads.join("\n\n")
    navigator.clipboard.writeText(fullThread)
    toast({
      title: "Kopyalandı",
      description: "Tam thread panoya kopyalandı",
    })
  }

  const handleCopyTweet = (index: number) => {
    navigator.clipboard.writeText(threads[index])
    toast({
      title: "Kopyalandı",
      description: `${index + 1}. tweet kopyalandı`,
    })
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Thread Oluştur
          </CardTitle>
          <CardDescription>
            Birden fazla bağlı tweet'i içeren viral thread'ler
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Konu *</label>
            <Input
              placeholder="örn: Startup kurma rehberi, Yapay zeka geleceği..."
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Tweet Sayısı</label>
              <select
                value={tweetCount}
                onChange={(e) => setTweetCount(parseInt(e.target.value))}
                className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                {[3, 5, 7, 10, 15].map((n) => (
                  <option key={n} value={n}>{n} tweet</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Stil</label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                {THREAD_STYLES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Dil</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="tr">🇹🇷 Türkçe</option>
              <option value="en">🇬🇧 English</option>
            </select>
          </div>

          <Button
            onClick={handleGenerate}
            disabled={loading || !topic.trim()}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Oluşturuluyor...
              </>
            ) : (
              <>
                <MessageSquare className="w-4 h-4 mr-2" />
                Thread Oluştur
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader>
          <CardTitle>Oluşturulan Thread</CardTitle>
          {threads.length > 0 && (
            <CardDescription>
              {threads.length} tweet, {threads.reduce((sum, t) => sum + t.length, 0)} karakter
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          {threads.length > 0 ? (
            <div className="space-y-4">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyAll}
                className="w-full"
              >
                <Copy className="w-4 h-4 mr-2" />
                Tümünü Kopyala
              </Button>

              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {threads.map((tweet, index) => (
                  <div
                    key={index}
                    className="p-4 border rounded-lg hover:bg-muted/50 transition-colors group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-xs font-mono text-muted-foreground">
                        {index + 1}/{threads.length}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopyTweet(index)}
                        className="opacity-0 group-hover:opacity-100"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                    <p className="text-sm whitespace-pre-wrap mt-1">{tweet}</p>
                    <div className="text-xs text-muted-foreground mt-2">
                      {tweet.length} karakter
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <MessageSquare className="w-12 h-12 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground">
                Thread sonuçları burada görünecek
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
