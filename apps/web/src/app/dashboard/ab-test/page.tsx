import { Metadata } from "next"
import { ABTestCreator } from "@/components/abtest/ABTestCreator"

export const metadata: Metadata = {
  title: "A/B Test | X Algorithm Tweet Generator",
  description: "Tweet varyasyonlarını test edin ve en iyisini bulun",
}

export default function ABTestPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">A/B Test Sistemi</h1>
        <p className="text-muted-foreground">
          Farklı tweet varyasyonlarını test ederek en yüksek etkileşimi alın
        </p>
      </div>

      <ABTestCreator />
    </div>
  )
}
