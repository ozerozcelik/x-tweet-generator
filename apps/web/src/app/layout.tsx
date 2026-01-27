import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { QueryProvider } from "@/components/providers/QueryProvider"
import { Toaster } from "@/components/ui/toaster"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import { NextAuthProvider } from "@/components/providers/NextAuthProvider"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "X Algorithm Tweet Generator | AI-Powered Tweet Optimization",
  description: "X'in For You algoritmasına göre tweetlerinizi optimize edin. AI ile tweet üretin, analiz edin ve planlayın.",
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getServerSession(authOptions)

  return (
    <html lang="tr" suppressHydrationWarning>
      <body className={inter.className}>
        <NextAuthProvider session={session}>
          <QueryProvider>
            {children}
            <Toaster />
          </QueryProvider>
        </NextAuthProvider>
      </body>
    </html>
  )
}
