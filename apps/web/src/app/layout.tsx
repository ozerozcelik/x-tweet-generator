import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { SupabaseProvider } from "@/components/providers/SupabaseProvider"
import { QueryProvider } from "@/components/providers/QueryProvider"
import { Toaster } from "@/components/ui/toaster"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "X Algorithm Tweet Generator | AI-Powered Tweet Optimization",
  description: "X'in For You algoritmasına göre tweetlerinizi optimize edin. AI ile tweet üretin, analiz edin ve planlayın.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="tr" suppressHydrationWarning>
      <body className={inter.className}>
        <SupabaseProvider>
          <QueryProvider>
            {children}
            <Toaster />
          </QueryProvider>
        </SupabaseProvider>
      </body>
    </html>
  )
}
