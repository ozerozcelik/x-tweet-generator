"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { useToast } from "@/hooks/use-toast"
import { api } from "@/lib/api"
import { Calendar, Clock, Trash2, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export function ScheduleCalendar() {
  const { toast } = useToast()

  const [content, setContent] = useState("")
  const [scheduledFor, setScheduledFor] = useState("")
  const [loading, setLoading] = useState(false)
  const [scheduledTweets, setScheduledTweets] = useState<any[]>([])

  const loadScheduledTweets = async () => {
    try {
      const tweets = await api.getScheduledTweets()
      setScheduledTweets(tweets)
    } catch (error) {
      console.error("Failed to load scheduled tweets:", error)
    }
  }

  const handleSchedule = async () => {
    if (!content.trim()) {
      toast({
        variant: "destructive",
        title: "Tweet gereklidir",
        description: "Lütfen planlanacak tweet'i girin",
      })
      return
    }

    if (!scheduledFor) {
      toast({
        variant: "destructive",
        title: "Tarih seçilmelidir",
        description: "Lütfen bir tarih ve saat seçin",
      })
      return
    }

    setLoading(true)

    try {
      await api.scheduleTweet({
        content: content.trim(),
        scheduled_for: new Date(scheduledFor).toISOString(),
      })

      toast({
        title: "Tweet planlandı!",
        description: "Tweet otomatik olarak paylaşılacak",
      })

      setContent("")
      setScheduledFor("")
      loadScheduledTweets()
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Planlama başarısız",
        description: error.message || "Bir hata oluştu",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await api.deleteScheduledTweet(id)
      toast({
        title: "Planlama iptal edildi",
      })
      loadScheduledTweets()
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "İptal başarısız",
        description: error.message,
      })
    }
  }

  // Load on mount
  useState(() => {
    loadScheduledTweets()
  })

  const getDateTimeLocal = (date: Date) => {
    const offset = date.getTimezoneOffset() * 60000
    const local = new Date(date.getTime() - offset)
    return local.toISOString().slice(0, 16)
  }

  // Get default datetime (now + 1 hour)
  const defaultDateTime = getDateTimeLocal(new Date(Date.now() + 60 * 60 * 1000))

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Schedule Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Tweet Planla
          </CardTitle>
          <CardDescription>
            Tweet'i otomatik paylaşmak için planlayın
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Tweet</label>
            <Textarea
              placeholder="Planlanacak tweet..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={6}
              className="resize-none"
            />
            <div className="text-xs text-muted-foreground">
              {content.length} karakter
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Tarih ve Saat</label>
            <Input
              type="datetime-local"
              value={scheduledFor || defaultDateTime}
              onChange={(e) => setScheduledFor(e.target.value)}
              min={getDateTimeLocal(new Date())}
            />
          </div>

          <Button
            onClick={handleSchedule}
            disabled={loading || !content.trim()}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Planlanıyor...
              </>
            ) : (
              <>
                <Clock className="w-4 h-4 mr-2" />
                Tweet Planla
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Scheduled Tweets */}
      <Card>
        <CardHeader>
          <CardTitle>Planlanan Tweetler</CardTitle>
          <CardDescription>
            {scheduledTweets.length} tweet planlanmış
          </CardDescription>
        </CardHeader>
        <CardContent>
          {scheduledTweets.length > 0 ? (
            <div className="space-y-3">
              {scheduledTweets.map((tweet) => (
                <div
                  key={tweet.id}
                  className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <p className="text-sm mb-2 line-clamp-3">{tweet.content}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      {new Date(tweet.scheduled_for).toLocaleString("tr-TR", {
                        dateStyle: "short",
                        timeStyle: "short",
                      })}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(tweet.id)}
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Calendar className="w-12 h-12 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground">
                Henüz planlanmış tweet yok
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
