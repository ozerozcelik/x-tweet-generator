"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { api } from "@/lib/api"
import { FlaskConical, Plus, Trash2, Loader2, Trophy } from "lucide-react"
import { cn } from "@/lib/utils"

export function ABTestCreator() {
  const { toast } = useToast()

  const [campaignName, setCampaignName] = useState("")
  const [variants, setVariants] = useState(["", ""])
  const [loading, setLoading] = useState(false)
  const [campaigns, setCampaigns] = useState<any[]>([])

  const loadCampaigns = async () => {
    try {
      const result = await api.getAbCampaigns()
      setCampaigns(result)
    } catch (error) {
      console.error("Failed to load campaigns:", error)
    }
  }

  const addVariant = () => {
    if (variants.length < 5) {
      setVariants([...variants, ""])
    }
  }

  const removeVariant = (index: number) => {
    if (variants.length > 2) {
      setVariants(variants.filter((_, i) => i !== index))
    }
  }

  const updateVariant = (index: number, value: string) => {
    const newVariants = [...variants]
    newVariants[index] = value
    setVariants(newVariants)
  }

  const handleCreate = async () => {
    if (!campaignName.trim()) {
      toast({
        variant: "destructive",
        title: "Kampanya adı gereklidir",
        description: "Lütfen kampanyaya bir isim verin",
      })
      return
    }

    const validVariants = variants.filter((v) => v.trim().length > 0)

    if (validVariants.length < 2) {
      toast({
        variant: "destructive",
        title: "En az 2 varyasyon gerekli",
        description: "Lütfen en az 2 farklı tweet girin",
      })
      return
    }

    setLoading(true)

    try {
      await api.createAbCampaign({
        name: campaignName.trim(),
        variants: validVariants,
      })

      toast({
        title: "A/B Testi oluşturuldu!",
        description: "Kampanyalar sekmesinden sonuçları takip edebilirsiniz",
      })

      setCampaignName("")
      setVariants(["", ""])
      loadCampaigns()
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

  const loadCampaignsOnce = useState(() => {
    loadCampaigns()
  })[1]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running": return "bg-blue-100 text-blue-700"
      case "completed": return "bg-green-100 text-green-700"
      case "paused": return "bg-yellow-100 text-yellow-700"
      default: return "bg-gray-100 text-gray-700"
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "running": return "Aktif"
      case "completed": return "Tamamlandı"
      case "paused": return "Duraklatıldı"
      default: return status
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Create Campaign */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FlaskConical className="w-5 h-5" />
            Yeni A/B Testi
          </CardTitle>
          <CardDescription>
            Farklı tweet varyasyonlarını test edin
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Kampanya Adı</label>
            <Input
              placeholder="örn: Cuma tweet testi"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Tweet Varyasyonları</label>
            {variants.map((variant, index) => (
              <div key={index} className="flex gap-2">
                <Textarea
                  placeholder={`Varyasyon ${index + 1}...`}
                  value={variant}
                  onChange={(e) => updateVariant(index, e.target.value)}
                  rows={3}
                  className="resize-none flex-1"
                />
                {variants.length > 2 && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeVariant(index)}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                )}
              </div>
            ))}
            {variants.length < 5 && (
              <Button
                variant="outline"
                size="sm"
                onClick={addVariant}
                className="w-full"
              >
                <Plus className="w-4 h-4 mr-2" />
                Varyasyon Ekle
              </Button>
            )}
          </div>

          <Button
            onClick={handleCreate}
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Oluşturuluyor...
              </>
            ) : (
              <>
                <FlaskConical className="w-4 h-4 mr-2" />
                Testi Başlat
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Campaigns List */}
      <Card>
        <CardHeader>
          <CardTitle>A/B Testleri</CardTitle>
          <CardDescription>
            {campaigns.length} aktif kampanya
          </CardDescription>
        </CardHeader>
        <CardContent>
          {campaigns.length > 0 ? (
            <div className="space-y-3">
              {campaigns.map((campaign) => (
                <div
                  key={campaign.id}
                  className="p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => window.location.href = `/dashboard/ab-test/${campaign.id}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold">{campaign.name}</h3>
                    <span className={cn(
                      "text-xs px-2 py-1 rounded-full",
                      getStatusColor(campaign.status)
                    )}>
                      {getStatusLabel(campaign.status)}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {new Date(campaign.created_at).toLocaleDateString("tr-TR")}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FlaskConical className="w-12 h-12 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground">
                Henüz A/B testi yok
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
