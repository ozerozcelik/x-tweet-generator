// Turso Database Client
// https://docs.turso.tech/sdk/reference/client

import { createClient } from '@libsql/client';
import type { TweetAnalysis, Profile, Tweet } from '@/types';

const tursoUrl = process.env.TURSO_URL || '';
const tursoToken = process.env.TURSO_AUTH_TOKEN || '';

if (!tursoUrl || !tursoToken) {
  console.warn('TURSO_URL or TURSO_AUTH_TOKEN not set');
}

export const turso = createClient({
  url: tursoUrl,
  authToken: tursoToken,
});

// Database helper functions
export const db = {
  // Users
  async getUserById(id: string) {
    const result = await turso.execute({
      sql: 'SELECT * FROM users WHERE id = ?',
      args: [id]
    });
    return result.rows[0];
  },

  async getUserByEmail(email: string) {
    const result = await turso.execute({
      sql: 'SELECT * FROM users WHERE email = ?',
      args: [email]
    });
    return result.rows[0];
  },

  async createUser(data: {
    id: string;
    email: string;
    name?: string;
  }) {
    await turso.execute({
      sql: 'INSERT INTO users (id, email, name) VALUES (?, ?, ?)',
      args: [data.id, data.email, data.name || null]
    });
    return this.getUserById(data.id);
  },

  async updateUser(id: string, data: { name?: string; email?: string }) {
    const fields: string[] = [];
    const args: any[] = [];

    if (data.name) {
      fields.push('name = ?');
      args.push(data.name);
    }
    if (data.email) {
      fields.push('email = ?');
      args.push(data.email);
    }

    args.push(id);
    await turso.execute({
      sql: `UPDATE users SET ${fields.join(', ')}, updated_at = datetime('now') WHERE id = ?`,
      args
    });
    return this.getUserById(id);
  },

  // Profiles
  async getProfile(userId: string) {
    const result = await turso.execute({
      sql: 'SELECT * FROM profiles WHERE id = ?',
      args: [userId]
    });
    return result.rows[0];
  },

  async createProfile(data: {
    id: string;
    username?: string;
    x_username?: string;
  }) {
    await turso.execute({
      sql: `INSERT INTO profiles (id, username, x_username) VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET username = excluded.username`,
      args: [data.id, data.username || null, data.x_username || null]
    });
    return this.getProfile(data.id);
  },

  async updateProfile(userId: string, data: Partial<Omit<Profile, 'id' | 'created_at' | 'updated_at'>>) {
    // Whitelist of allowed columns to prevent SQL injection
    const allowedColumns = ['username', 'x_username', 'followers', 'following'] as const;
    const fields: string[] = [];
    const args: (string | number | null)[] = [];

    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && allowedColumns.includes(key as typeof allowedColumns[number])) {
        fields.push(`${key} = ?`);
        args.push(value);
      }
    });

    if (fields.length === 0) return this.getProfile(userId);

    args.push(userId);
    await turso.execute({
      sql: `UPDATE profiles SET ${fields.join(', ')}, updated_at = datetime('now') WHERE id = ?`,
      args
    });
    return this.getProfile(userId);
  },

  // Tweets
  async createTweet(data: {
    id: string;
    user_id: string;
    content: string;
    analysis?: string;
    status?: string;
  }) {
    await turso.execute({
      sql: `INSERT INTO tweets (id, user_id, content, analysis, status)
            VALUES (?, ?, ?, ?, ?)`,
      args: [
        data.id,
        data.user_id,
        data.content,
        data.analysis ? JSON.stringify(data.analysis) : null,
        data.status || 'draft'
      ]
    });
    return this.getTweetById(data.id);
  },

  async getTweetById(id: string) {
    const result = await turso.execute({
      sql: 'SELECT * FROM tweets WHERE id = ?',
      args: [id]
    });
    const row = result.rows[0];
    if (!row) return null;
    return {
      ...row,
      analysis: row.analysis ? JSON.parse(row.analysis as string) : null
    };
  },

  async getTweetsByUserId(userId: string, limit = 50) {
    const result = await turso.execute({
      sql: 'SELECT * FROM tweets WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
      args: [userId, limit]
    });
    return result.rows.map(row => ({
      ...row,
      analysis: row.analysis ? JSON.parse(row.analysis as string) : null
    }));
  },

  async updateTweet(id: string, data: Partial<Omit<Tweet, 'id' | 'user_id' | 'created_at' | 'updated_at'>>) {
    // Whitelist of allowed columns to prevent SQL injection
    const allowedColumns = ['content', 'analysis', 'status', 'scheduled_for'] as const;
    const fields: string[] = [];
    const args: (string | number | null | TweetAnalysis)[] = [];

    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && allowedColumns.includes(key as typeof allowedColumns[number])) {
        fields.push(`${key} = ?`);
        args.push(key === 'analysis' && value ? JSON.stringify(value) : value);
      }
    });

    if (fields.length === 0) return this.getTweetById(id);

    args.push(id);
    await turso.execute({
      sql: `UPDATE tweets SET ${fields.join(', ')}, updated_at = datetime('now') WHERE id = ?`,
      args
    });
    return this.getTweetById(id);
  },

  async deleteTweet(id: string) {
    await turso.execute({
      sql: 'DELETE FROM tweets WHERE id = ?',
      args: [id]
    });
  },

  // A/B Campaigns
  async createCampaign(data: {
    id: string;
    user_id: string;
    name: string;
  }) {
    await turso.execute({
      sql: 'INSERT INTO ab_campaigns (id, user_id, name) VALUES (?, ?, ?)',
      args: [data.id, data.user_id, data.name]
    });
    return this.getCampaignById(data.id);
  },

  async getCampaignById(id: string) {
    const result = await turso.execute({
      sql: 'SELECT * FROM ab_campaigns WHERE id = ?',
      args: [id]
    });
    return result.rows[0];
  },

  async getCampaignsByUserId(userId: string) {
    const result = await turso.execute({
      sql: 'SELECT * FROM ab_campaigns WHERE user_id = ? ORDER BY created_at DESC',
      args: [userId]
    });
    return result.rows;
  },

  // Style Analyses
  async createStyleAnalysis(data: {
    id: string;
    user_id: string;
    analysis_data: Record<string, unknown>;
  }) {
    await turso.execute({
      sql: 'INSERT INTO style_analyses (id, user_id, analysis_data) VALUES (?, ?, ?)',
      args: [data.id, data.user_id, JSON.stringify(data.analysis_data)]
    });
    return this.getStyleAnalysisById(data.id);
  },

  async getStyleAnalysisById(id: string) {
    const result = await turso.execute({
      sql: 'SELECT * FROM style_analyses WHERE id = ?',
      args: [id]
    });
    const row = result.rows[0];
    if (!row) return null;
    return {
      ...row,
      analysis_data: JSON.parse(row.analysis_data as string)
    };
  },

  async getLatestStyleAnalysis(userId: string) {
    const result = await turso.execute({
      sql: 'SELECT * FROM style_analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
      args: [userId]
    });
    const row = result.rows[0];
    if (!row) return null;
    return {
      ...row,
      analysis_data: JSON.parse(row.analysis_data as string)
    };
  },

  // API Usage tracking
  async trackUsage(data: {
    id: string;
    user_id?: string;
    endpoint: string;
    tokens_used?: number;
  }) {
    await turso.execute({
      sql: 'INSERT INTO api_usage (id, user_id, endpoint, tokens_used) VALUES (?, ?, ?, ?)',
      args: [
        data.id,
        data.user_id || null,
        data.endpoint,
        data.tokens_used || 0
      ]
    });
  }
};

export type Database = typeof db;
