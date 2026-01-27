-- X Tweet Generator Database Schema
-- Turso (LibSQL/SQLite) Migration

-- Users table (since Turso doesn't have built-in auth)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    name TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Profiles table
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    username TEXT,
    x_username TEXT,
    followers INTEGER DEFAULT 0,
    following INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0,
    total_posts INTEGER DEFAULT 0,
    avg_like_rate REAL DEFAULT 0.0100,
    account_age_years REAL DEFAULT 1.0,
    country TEXT DEFAULT 'TR',
    niche TEXT DEFAULT 'genel',
    bio TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Tweets table
CREATE TABLE IF NOT EXISTS tweets (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES profiles(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    analysis TEXT, -- JSON stored as TEXT
    status TEXT DEFAULT 'draft', -- draft, scheduled, posted, ab_test
    scheduled_for TEXT,
    posted_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- A/B Test campaigns
CREATE TABLE IF NOT EXISTS ab_campaigns (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'running', -- running, completed, paused
    started_at TEXT DEFAULT (datetime('now')),
    ended_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- A/B Test variants
CREATE TABLE IF NOT EXISTS ab_variants (
    id TEXT PRIMARY KEY,
    campaign_id TEXT REFERENCES ab_campaigns(id) ON DELETE CASCADE,
    tweet_id TEXT REFERENCES tweets(id) ON DELETE CASCADE,
    is_winner INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    retweets INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Style analyses
CREATE TABLE IF NOT EXISTS style_analyses (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES profiles(id) ON DELETE CASCADE,
    analysis_data TEXT NOT NULL, -- JSON stored as TEXT
    created_at TEXT DEFAULT (datetime('now'))
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES profiles(id) ON DELETE SET NULL,
    endpoint TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tweets_user_id ON tweets(user_id);
CREATE INDEX IF NOT EXISTS idx_tweets_status ON tweets(status);
CREATE INDEX IF NOT EXISTS idx_tweets_scheduled_for ON tweets(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at);
CREATE INDEX IF NOT EXISTS idx_ab_campaigns_user_id ON ab_campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_ab_variants_campaign_id ON ab_variants(campaign_id);
CREATE INDEX IF NOT EXISTS idx_style_analyses_user_id ON style_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage(created_at);

-- Insert a demo user for testing (remove in production)
INSERT OR IGNORE INTO users (id, email, name)
VALUES ('demo-user-id', 'demo@example.com', 'Demo User');

INSERT OR IGNORE INTO profiles (id, username, x_username, followers, following)
VALUES ('demo-user-id', 'demo', 'demouser', 1000, 500);
