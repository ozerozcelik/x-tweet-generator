// Shared TypeScript type definitions

export interface TweetAnalysis {
  score: number;
  phoenix_insights?: {
    tweetcred_status: string;
    engagement_debt_status: string;
    author_diversity_status: string;
    golden_hour_status: string;
  };
  engagement_prediction?: {
    reply: number;
    repost: number;
    favorite: number;
    quote: number;
    follow: number;
    dwell: number;
  };
  breakdown?: {
    baseScore: number;
    profileBoost: number;
    contentBonus: number;
    viralBonus: number;
    timingBonus: number;
    authorDiversityPenalty?: number;
  };
  distributionRate?: number;
  warnings?: string[];
  strengths?: string[];
  weaknesses?: string[];
  suggestions?: string[];
}

export interface Tweet {
  id: string;
  user_id: string;
  content: string;
  analysis?: TweetAnalysis | null;
  status: 'draft' | 'scheduled' | 'posted';
  scheduled_for?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Profile {
  id: string;
  username?: string | null;
  x_username?: string | null;
  followers?: number;
  following?: number;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ABCampaign {
  id: string;
  user_id: string;
  name: string;
  status: 'active' | 'completed' | 'paused';
  created_at: string;
  updated_at: string;
}

export interface StyleAnalysis {
  id: string;
  user_id: string;
  analysis_data: {
    style?: string;
    tone?: string;
    patterns?: string[];
    common_topics?: string[];
  };
  created_at: string;
}

export interface GenerateTweetRequest {
  topic: string;
  style?: string;
  tone?: string;
  length?: string;
  language?: string;
  include_cta?: boolean;
  include_emoji?: boolean;
  custom_instructions?: string;
}

export interface GenerateTweetResponse {
  content: string;
  analysis: TweetAnalysis;
}

export interface ApiError {
  error: string;
  message?: string;
}
