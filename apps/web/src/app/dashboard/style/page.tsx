import { Metadata } from "next"
import { StyleAnalyzer } from "@/components/style/StyleAnalyzer"

export const metadata: Metadata = {
  title: "Stil Analizi | X Algorithm Tweet Generator",
  description: "Tweet stilinizi analiz edin ve kişiselleştirilmiş tweet'ler üretin",
}

export default function StylePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Stil Analizi</h1>
        <p className="text-muted-foreground">
          Tweetlerinizi analiz ederek yazım stilinizi öğrenin
        </p>
      </div>

      <StyleAnalyzer />
    </div>
  )
}
