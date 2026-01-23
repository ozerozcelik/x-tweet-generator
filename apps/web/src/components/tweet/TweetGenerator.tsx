"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { useToast } from "@/hooks/use-toast"
import { api } from "@/lib/api"
import { Loader2, Sparkles, Copy, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"

const LANGUAGES = [
  { value: "tr", label: "🇹🇷 Türkçe" },
  { value: "en", label: "🇬🇧 English" },
  { value: "de", label: "🇩🇪 Deutsch" },
  { value: "fr", label: "🇫🇷 Français" },
  { value: "es", label: "🇪🇸 Español" },
  { value: "ar", label: "🇸🇦 العربية" },
  { value: "zh", label: "🇨🇳 中文" },
  { value: "ja", label: "🇯🇵 日本語" },
]

const STYLES = [
  { value: "casual", label: "😎 Casual" },
  { value: "professional", label: "🎩 Profesyonel" },
  { value: "provocative", label: "🔥 Provokatif" },
  { value: "storytelling", label: "📖 Hikaye" },
  { value: "educational", label: "🎓 Eğitici" },
]

const TONES = [
  { value: "engaging", label: "💬 Etkileşimci" },
  { value: "controversial", label: "⚡ Tartışmalı" },
  { value: "inspirational", label: "✨ İlham Verici" },
  { value: "humorous", label: "😄 Esprili" },
  { value: "raw", label: "💯 Ham/Dürüst" },
]

const LENGTHS = [
  { value: "short", label: "📝 Kısa (100-200)" },
  { value: "medium", label: "📄 Orta (300-600)" },
  { value: "long", label: "📰 Uzun (800-1500)" },
  { value: "epic", label: "📚 Epik (2000-4000)" },
]

export function TweetGenerator() {
  const { toast } = useToast()

  const [topic, setTopic] = useState("")
  const [style, setStyle] = useState("casual")
  const [tone, setTone] = useState("engaging")
  const [length, setLength] = useState("medium")
  const [language, setLanguage] = useState("tr")
  const [includeCta, setIncludeCta] = useState(true)
  const [includeEmoji, setIncludeEmoji] = useState(true)
  const [customInstructions, setCustomInstructions] = useState("")

  const [generatedTweet, setGeneratedTweet] = useState("")
  const [analysis, setAnalysis] = useState<any>(null)
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
    setGeneratedTweet("")
    setAnalysis(null)

    try {
      const result = await api.generateTweet({
        topic: topic.trim(),
        style,
        tone,
        length,
        language,
        include_cta: includeCta,
        include_emoji: includeEmoji,
        custom_instructions: customInstructions || undefined,
      })

      setGeneratedTweet(result.content)
      setAnalysis(result.analysis)

      toast({
        title: "Tweet üretildi!",
        description: `${result.content.length} karakter`,
      })
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Üretim başarısız",
        description: error.message || "Bir hata oluştu",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedTweet)
    toast({
      title: "Kopyalandı",
      description: "Tweet panoya kopyalandı",
    })
  }

  const handleRegenerate = () => {
    handleGenerate()
  }

  const getScoreColor = (score: number) => {
    if (score >= 70) return "text-green-500"
    if (score >= 50) return "text-yellow-500"
    return "text-red-500"
  }

  const getScoreLabel = (score: number) => {
    if (score >= 70) return "Mükemmel"
    if (score >= 50) return "İyi"
    return "Geliştirilmeli"
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Input Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            Tweet Üret
          </CardTitle>
          <CardDescription>
            AI ile viral potansiyelli tweetler üretin
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Topic */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Konu *</label>
            <Input
              placeholder="örn: yapay zeka, startup, kariyer..."
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !loading && handleGenerate()}
            />
          </div>

          {/* Style & Tone */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Stil</label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                {STYLES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Ton</label>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                {TONES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Length & Language */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Uzunluk</label>
              <select
                value={length}
                onChange={(e) => setLength(e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                {LENGTHS.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Dil</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                {LANGUAGES.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Options */}
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={includeCta}
                onChange={(e) => setIncludeCta(e.target.checked)}
                className="rounded"
              />
              Call to Action
            </label>

            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={includeEmoji}
                onChange={(e) => setIncludeEmoji(e.target.checked)}
                className="rounded"
              />
              Emoji
            </label>
          </div>

          {/* Custom Instructions */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Özel Talimatlar (Opsiyonel)</label>
            <Textarea
              placeholder="örn: Benim sektörüm fintech, hedef kitle yatırımcılar..."
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              rows={3}
            />
          </div>

          {/* Generate Button */}
          <Button
            onClick={handleGenerate}
            disabled={loading || !topic.trim()}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Üretiliyor...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Tweet Üret
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Result Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Üretilen Tweet</CardTitle>
          <CardDescription>
            {generatedTweet && `${generatedTweet.length} karakter`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {generatedTweet ? (
            <div className="space-y-6">
              {/* Tweet Content */}
              <div className="relative">
                <Textarea
                  value={generatedTweet}
                  onChange={(e) => setGeneratedTweet(e.target.value)}
                  rows={10}
                  className="resize-none"
                />
                <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
                  {generatedTweet.length}/280
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopy}
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Kopyala
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRegenerate}
                  disabled={loading}
                >
                  <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
                  Yeniden Üret
                </Button>
              </div>

              {/* Analysis */}
              {analysis && (
                <div className="space-y-4 pt-4 border-t">
                  <h3 className="font-semibold">Algoritma Analizi</h3>

                  {/* Score */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Skor:</span>
                    <div className="flex items-center gap-2">
                      <span className={cn("text-2xl font-bold", getScoreColor(analysis.score))}>
                        {analysis.score}/100
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {getScoreLabel(analysis.score)}
                      </span>
                    </div>
                  </div>

                  {/* Strengths */}
                  {analysis.strengths && analysis.strengths.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-green-600">✓ Güçlü Yönler:</span>
                      <ul className="mt-1 space-y-1">
                        {analysis.strengths.map((s: string, i: number) => (
                          <li key={i} className="text-sm text-muted-foreground">
                            • {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Weaknesses */}
                  {analysis.weaknesses && analysis.weaknesses.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-red-600">✗ Zayıf Yönler:</span>
                      <ul className="mt-1 space-y-1">
                        {analysis.weaknesses.map((w: string, i: number) => (
                          <li key={i} className="text-sm text-muted-foreground">
                            • {w}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Suggestions */}
                  {analysis.suggestions && analysis.suggestions.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-blue-600">💡 Öneriler:</span>
                      <ul className="mt-1 space-y-1">
                        {analysis.suggestions.map((s: string, i: number) => (
                          <li key={i} className="text-sm text-muted-foreground">
                            • {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Sparkles className="w-12 h-12 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground">
                Tweet üretmek için bir konu girin
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
