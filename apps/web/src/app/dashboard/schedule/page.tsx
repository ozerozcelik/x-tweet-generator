import { Metadata } from "next"
import { ScheduleCalendar } from "@/components/scheduling/ScheduleCalendar"

export const metadata: Metadata = {
  title: "Tweet Planlama | X Algorithm Tweet Generator",
  description: "Tweetlerinizi otomatik paylaşım için planlayın",
}

export default function SchedulePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Tweet Planlama</h1>
        <p className="text-muted-foreground">
          En iyi zamanlarda tweet paylaşmak için planlayın
        </p>
      </div>

      <ScheduleCalendar />
    </div>
  )
}
