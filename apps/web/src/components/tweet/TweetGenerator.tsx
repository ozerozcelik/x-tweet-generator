"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { useToast } from "@/hooks/use-toast"
import { api } from "@/lib/api"
import { Loader2, Sparkles, Copy, RefreshCw, Save } from "lucide-react"
import { cn } from "@/lib/utils"
import type { TweetAnalysis } from "@/types"

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
  { value: "story", label: "📖 Hikaye" },
  { value: "educational", label: "🎓 Eğitici" },
  { value: "list", label: "📝 Liste" },
  { value: "question", label: "❓ Soru" },
  { value: "motivational", label: "💪 Motivasyon" },
  { value: "controversial", label: "⚡ Tartışmalı" },
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
  const [analysis, setAnalysis] = useState<TweetAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

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
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Bir hata oluştu"
      toast({
        variant: "destructive",
        title: "Üretim başarısız",
        description: errorMessage,
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

  const handleSave = async () => {
    if (!generatedTweet.trim()) {
      toast({
        variant: "destructive",
        title: "Tweet yok",
        description: "Önce bir tweet üretin",
      })
      return
    }

    setSaving(true)

    try {
      await api.saveTweet({
        content: generatedTweet,
        analysis: analysis || undefined,
        status: "draft",
      })

      toast({
        title: "Tweet kaydedildi!",
        description: "Analytics sayfasından görüntüleyebilirsiniz",
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Bir hata oluştu"
      toast({
        variant: "destructive",
        title: "Kaydetme başarısız",
        description: errorMessage,
      })
    } finally {
      setSaving(false)
    }
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

  const getScoreBadgeColor = (score: number) => {
    if (score >= 70) return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
    if (score >= 50) return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
    return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
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
                  {generatedTweet.length}/25.000
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
                  onClick={handleSave}
                  disabled={saving || !generatedTweet}
                >
                  <Save className={cn("w-4 h-4 mr-2", saving && "animate-spin")} />
                  {saving ? "Kaydediliyor..." : "Kaydet"}
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

              {/* Phoenix Analysis */}
              {analysis && (
                <div className="space-y-4 pt-4 border-t">
                  <h3 className="font-semibold flex items-center gap-2">
                    <span>🔥</span> Phoenix Algoritma Analizi
                  </h3>

                  {/* Score */}
                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <span className="text-sm font-medium">Viral Skor:</span>
                    <div className="flex items-center gap-2">
                      <span className={cn("text-2xl font-bold", getScoreColor(analysis.score))}>
                        {analysis.score}/100
                      </span>
                      <span className={cn("text-xs px-2 py-1 rounded-full", getScoreBadgeColor(analysis.score))}>
                        {getScoreLabel(analysis.score)}
                      </span>
                    </div>
                  </div>

                  {/* Phoenix Insights */}
                  {analysis.phoenix_insights && (
                    <div className="space-y-2 p-3 bg-orange-50 dark:bg-orange-950/20 rounded-lg">
                      <span className="text-sm font-medium text-orange-700 dark:text-orange-400">📊 Phoenix Insights:</span>
                      <ul className="mt-2 space-y-1">
                        <li className="text-xs text-muted-foreground flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-orange-500"></span>
                          {analysis.phoenix_insights.tweetcred_status}
                        </li>
                        <li className="text-xs text-muted-foreground flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-orange-500"></span>
                          {analysis.phoenix_insights.engagement_debt_status}
                        </li>
                        <li className="text-xs text-muted-foreground flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-orange-500"></span>
                          {analysis.phoenix_insights.author_diversity_status}
                        </li>
                        <li className="text-xs text-muted-foreground flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-orange-500"></span>
                          {analysis.phoenix_insights.golden_hour_status}
                        </li>
                      </ul>
                    </div>
                  )}

                  {/* Warnings */}
                  {analysis.warnings && analysis.warnings.length > 0 && (
                    <div className="p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg">
                      <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">⚠️ Uyarılar:</span>
                      <ul className="mt-2 space-y-1">
                        {analysis.warnings.map((w: string, i: number) => (
                          <li key={i} className="text-xs text-muted-foreground">
                            • {w}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Engagement Prediction - 15 Actions */}
                  {analysis.engagement_prediction && (
                    <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                      <span className="text-sm font-medium text-blue-700 dark:text-blue-400">📈 Etkileşim Tahmini (15 Eylem):</span>
                      <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                        <div className="flex justify-between">
                          <span>Reply (+1.5):</span>
                          <span className="font-medium">{(analysis.engagement_prediction.reply * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Repost (+1.2):</span>
                          <span className="font-medium">{(analysis.engagement_prediction.repost * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Like (+0.3):</span>
                          <span className="font-medium">{(analysis.engagement_prediction.favorite * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Quote (+1.3):</span>
                          <span className="font-medium">{(analysis.engagement_prediction.quote * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Follow (+5.0):</span>
                          <span className="font-medium">{(analysis.engagement_prediction.follow * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Dwell (+1.0):</span>
                          <span className="font-medium">{(analysis.engagement_prediction.dwell * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Breakdown */}
                  {analysis.breakdown && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                      <span className="text-sm font-medium">🔍 Skor Breakdown:</span>
                      <div className="mt-2 space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span>Base Score:</span>
                          <span className="font-medium">{analysis.breakdown.baseScore.toFixed(0)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Profile Boost:</span>
                          <span className="font-medium">x{analysis.breakdown.profileBoost.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Content Bonus:</span>
                          <span className="font-medium">x{analysis.breakdown.contentBonus.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Viral Bonus:</span>
                          <span className="font-medium">x{analysis.breakdown.viralBonus.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Timing Bonus:</span>
                          <span className="font-medium">x{analysis.breakdown.timingBonus.toFixed(2)}</span>
                        </div>
                        {analysis.breakdown.authorDiversityPenalty !== undefined && (
                          <div className="flex justify-between">
                            <span>Author Diversity:</span>
                            <span className={cn("font-medium", analysis.breakdown.authorDiversityPenalty < 1 ? "text-red-500" : "text-green-500")}>
                              x{analysis.breakdown.authorDiversityPenalty.toFixed(2)}
                            </span>
                          </div>
                        )}
                        <div className="flex justify-between text-muted-foreground">
                          <span>Distribution Rate:</span>
                          <span>{(analysis.distributionRate * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  )}

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
