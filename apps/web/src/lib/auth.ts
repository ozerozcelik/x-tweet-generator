// NextAuth Configuration with Turso database
import { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { db } from './db';

// Validate required environment variables
const nextAuthSecret = process.env.NEXTAUTH_SECRET;
if (!nextAuthSecret || nextAuthSecret === 'your-secret-key-change-in-production') {
  throw new Error('NEXTAUTH_SECRET must be set in environment variables with a strong random value');
}

// Simple password hashing for demo (use bcrypt in production)
async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(password + nextAuthSecret);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

async function verifyPassword(password: string, hashedPassword: string): Promise<boolean> {
  const hash = await hashPassword(password);
  return hash === hashedPassword;
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error('Email and password are required');
        }

        // Check for demo mode (set DEMO_MODE=true to enable auto-creation)
        const isDemoMode = process.env.DEMO_MODE === 'true';

        let user = await db.getUserByEmail(credentials.email);

        if (!user) {
          if (isDemoMode) {
            // Demo mode: auto-create user
            const userId = crypto.randomUUID();
            const hashedPassword = await hashPassword(credentials.password);

            user = await db.createUser({
              id: userId,
              email: credentials.email,
              name: credentials.email.split('@')[0]
            });

            // Store hashed password in a separate table or extend user table
            // For now, we'll skip password storage in this simplified version

            // Create profile
            await db.createProfile({
              id: userId,
              username: credentials.email.split('@')[0]
            });
          } else {
            // Production mode: require existing user
            throw new Error('Invalid email or password');
          }
        }

        // In production, verify password hash here
        // const isValidPassword = await verifyPassword(credentials.password, user.passwordHash);
        // if (!isValidPassword) {
        //   throw new Error('Invalid email or password');
        // }

        return {
          id: user.id as string,
          email: user.email as string,
          name: user.name as string || user.email as string
        };
      }
    })
  ],
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  pages: {
    signIn: '/auth/login',
    signOut: '/auth/login',
    error: '/auth/login',
  },
  callbacks: {
    async jwt({ token, user, account }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
      }
      return session;
    }
  },
  secret: nextAuthSecret
};

// Extend NextAuth types
declare module 'next-auth' {
  interface User {
    id: string;
  }
  interface Session {
    user: {
      id: string;
      email: string;
      name: string;
    };
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id: string;
  }
}
