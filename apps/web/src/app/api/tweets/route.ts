import { NextRequest, NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import { db } from "@/lib/db"
import type { Tweet, TweetAnalysis } from "@/types"

// Save Tweet
export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions)

  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { content, analysis, status = "draft" } = await req.json()

  if (!content) {
    return NextResponse.json({ error: "Content is required" }, { status: 400 })
  }

  const tweetId = crypto.randomUUID()

  await db.createTweet({
    id: tweetId,
    user_id: session.user.id,
    content,
    analysis: analysis || null,
    status
  })

  const tweet = await db.getTweetById(tweetId)

  return NextResponse.json({ tweet })
}

// Get user's tweets
export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions)

  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const searchParams = req.nextUrl.searchParams
  const limit = parseInt(searchParams.get("limit") || "50")

  const tweets = await db.getTweetsByUserId(session.user.id, limit)

  return NextResponse.json({ tweets })
}

// Update tweet
export async function PATCH(req: NextRequest) {
  const session = await getServerSession(authOptions)

  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { id, ...data } = await req.json()

  if (!id) {
    return NextResponse.json({ error: "Tweet ID is required" }, { status: 400 })
  }

  const tweet = await db.getTweetById(id)

  if (!tweet || (tweet as Tweet).user_id !== session.user.id) {
    return NextResponse.json({ error: "Tweet not found" }, { status: 404 })
  }

  const updated = await db.updateTweet(id, data)

  return NextResponse.json({ tweet: updated })
}

// Delete tweet
export async function DELETE(req: NextRequest) {
  const session = await getServerSession(authOptions)

  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const searchParams = req.nextUrl.searchParams
  const id = searchParams.get("id")

  if (!id) {
    return NextResponse.json({ error: "Tweet ID is required" }, { status: 400 })
  }

  const tweet = await db.getTweetById(id)

  if (!tweet || (tweet as Tweet).user_id !== session.user.id) {
    return NextResponse.json({ error: "Tweet not found" }, { status: 404 })
  }

  await db.deleteTweet(id)

  return NextResponse.json({ success: true })
}
