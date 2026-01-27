import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import { db } from "@/lib/db"
import { redirect } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Settings, Save } from "lucide-react"

async function updateProfile(formData: FormData) {
  "use server"

  const session = await getServerSession(authOptions)

  if (!session?.user?.id) {
    return { error: "Not authenticated" }
  }

  const profileData: any = {}
  const xUsername = formData.get("x_username")
  if (xUsername) profileData.x_username = xUsername

  const followers = formData.get("followers")
  if (followers) profileData.followers = parseInt(followers as string) || 0

  const following = formData.get("following")
  if (following) profileData.following = parseInt(following as string) || 0

  const totalPosts = formData.get("total_posts")
  if (totalPosts) profileData.total_posts = parseInt(totalPosts as string) || 0

  const avgLikeRate = formData.get("avg_like_rate")
  if (avgLikeRate) profileData.avg_like_rate = (parseFloat(avgLikeRate as string) || 1) / 100

  profileData.verified = formData.get("verified") === "on"

  await db.updateProfile(session.user.id, profileData)

  redirect("/dashboard/settings")
}

export default async function SettingsPage() {
  const session = await getServerSession(authOptions)
  const userId = session?.user?.id

  // Get profile
  const profile = userId ? await db.getProfile(userId) : null

  const followers = (profile as any)?.followers || 0
  const following = (profile as any)?.following || 0
  const verified = (profile as any)?.verified || false
  const totalPosts = (profile as any)?.total_posts || 0
  const avgLikeRate = ((profile as any)?.avg_like_rate || 0.01) * 100

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Ayarlar</h1>
        <p className="text-muted-foreground">
          Profil bilgilerinizi ve tercihlerinizi yönetin
        </p>
      </div>

      {/* Profile Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Profil Bilgileri
          </CardTitle>
          <CardDescription>
            X hesap bilgilerinizi girin - daha doğru analiz ve tahminler için
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form action={updateProfile} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="x_username">X Kullanıcı Adı</Label>
                <Input
                  id="x_username"
                  name="x_username"
                  placeholder="elonmusk (@ olmadan)"
                  defaultValue={(profile as any)?.x_username || ""}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="followers">Takipçi Sayısı</Label>
                <Input
                  id="followers"
                  name="followers"
                  type="number"
                  min="0"
                  defaultValue={followers}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="following">Takip Sayısı</Label>
                <Input
                  id="following"
                  name="following"
                  type="number"
                  min="0"
                  defaultValue={following}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="total_posts">Toplam Tweet</Label>
                <Input
                  id="total_posts"
                  name="total_posts"
                  type="number"
                  min="0"
                  defaultValue={totalPosts}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="avg_like_rate">Ort. Beğeni Oranı (%)</Label>
                <Input
                  id="avg_like_rate"
                  name="avg_like_rate"
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  defaultValue={avgLikeRate.toFixed(1)}
                />
                <p className="text-xs text-muted-foreground">
                  Beğeni / Görüntülenme oranı
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="verified">Doğrulanmış Hesap</Label>
                <div className="flex items-center gap-2 mt-2">
                  <input
                    id="verified"
                    name="verified"
                    type="checkbox"
                    defaultChecked={verified}
                    className="rounded"
                  />
                  <span className="text-sm">Mavi tik</span>
                </div>
              </div>
            </div>

            <Button type="submit">
              <Save className="w-4 h-4 mr-2" />
              Kaydet
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Account Info */}
      <Card>
        <CardHeader>
          <CardTitle>Hesap Bilgileri</CardTitle>
          <CardDescription>
            Oturum açtığınız hesap bilgileri
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">E-posta</span>
            <span className="text-sm font-medium">{session?.user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">ID</span>
            <span className="text-sm font-medium">{session?.user?.id?.slice(0, 8)}...</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
