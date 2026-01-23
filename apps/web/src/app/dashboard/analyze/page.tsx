import { Metadata } from "next"
import { TweetAnalyzer } from "@/components/tweet/TweetAnalyzer"

export const metadata: Metadata = {
  title: "Tweet Analizi | X Algorithm Tweet Generator",
  description: "X algoritmasına göre tweet'inizi analiz edin",
}

export default function AnalyzePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Tweet Analizi</h1>
        <p className="text-muted-foreground">
          X'in For You algoritmasına göre tweet'inizi analiz edin
        </p>
      </div>

      <TweetAnalyzer />
    </div>
  )
}
