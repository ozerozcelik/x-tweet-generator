import { Metadata } from "next"
import { TweetGenerator } from "@/components/tweet/TweetGenerator"

export const metadata: Metadata = {
  title: "Tweet Üret | X Algorithm Tweet Generator",
  description: "AI ile viral potansiyelli tweetler üretin",
}

export default function GeneratePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">AI Tweet Üret</h1>
        <p className="text-muted-foreground">
          Claude AI ile X algoritmasına optimize edilmiş tweetler üretin
        </p>
      </div>

      <TweetGenerator />
    </div>
  )
}
