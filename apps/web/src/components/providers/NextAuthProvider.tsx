"use client"

import { SessionProvider as NextAuthSessionProvider } from "next-auth/react"

export function NextAuthProvider({
  children,
  session
}: {
  children: React.ReactNode
  session: any
}) {
  return (
    <NextAuthSessionProvider session={session}>
      {children}
    </NextAuthSessionProvider>
  )
}
