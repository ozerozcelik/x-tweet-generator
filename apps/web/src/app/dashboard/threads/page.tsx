import { Metadata } from "next"
import { ThreadGenerator } from "@/components/thread/ThreadGenerator"

export const metadata: Metadata = {
  title: "Thread Oluştur | X Algorithm Tweet Generator",
  description: "Viral potansiyelli thread'ler oluşturun",
}

export default function ThreadPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Thread Oluşturucu</h1>
        <p className="text-muted-foreground">
          Birden fazla bağlı tweet'ten oluşan viral thread'ler oluşturun
        </p>
      </div>

      <ThreadGenerator />
    </div>
  )
}
