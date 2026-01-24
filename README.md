# X Algorithm Tweet Generator v2.0

Modern full-stack X (Twitter) algoritmasına dayalı tweet üretim ve optimizasyon sistemi.

## 🏗️ Teknik Stack

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Supabase SSR** - Authentication & database
- **React Query** - Data fetching
- **Recharts** - Analytics charts

### Backend
- **FastAPI** - Python API framework
- **Pydantic** - Data validation
- **Anthropic Claude** - AI tweet generation
- **Supabase** - Database & Auth
- **APScheduler** - Scheduled tasks

### Database
- **Supabase PostgreSQL** - Managed database with RLS

## 📁 Proje Yapısı

```
x-tweet-generator/
├── apps/
│   ├── web/                    # Next.js Frontend
│   │   ├── src/
│   │   │   ├── app/            # App Router pages
│   │   │   ├── components/     # React components
│   │   │   ├── lib/            # Utilities & API client
│   │   │   └── hooks/          # React hooks
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── api/                    # FastAPI Backend
│   │   ├── app/
│   │   │   ├── api/v1/         # API endpoints
│   │   │   ├── core/           # Config & deps
│   │   │   ├── models/         # Pydantic models
│   │   │   ├── services/       # Business logic
│   │   │   └── main.py
│   │   └── requirements.txt
│   └── database/               # Supabase migrations
│       └── migrations/
├── package.json                # Root package.json
├── turbo.json                  # Turborepo config
└── .env.example                # Environment template
```

## 🚀 Kurulum

### 1. Gereksinimler

- Node.js 18+
- Python 3.11+
- Supabase hesabı
- Anthropic API key

### 2. Supabase Projesi Oluştur

1. [supabase.com](https://supabase.com) adresinde proje oluşturun
2. SQL Editor'da `apps/database/migrations/001_initial_schema.sql` dosyasını çalıştırın
3. Project Settings > API'den URL ve key'leri alın

### 3. Environment Variables

`.env` dosyası oluşturun:

```bash
cp .env.example .env
```

`.env` dosyasını doldurun:
```env
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
ANTHROPIC_API_KEY=your-anthropic-api-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Kurulum

```bash
# Root dependencies
npm install

# Frontend
cd apps/web
npm install

# Backend (Python venv önerilir)
cd ../api
pip install -r requirements.txt
```

### 5. Çalıştırma

```bash
# Terminal 1 - Frontend
cd apps/web
npm run dev

# Terminal 2 - Backend
cd apps/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Uygulamalar:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📊 Özellikler

### ✅ Phase 1 (Tamamlandı)
- Monorepo yapısı
- Next.js + FastAPI backend
- Supabase database schema
- Temel UI bileşenleri

### 🔨 Phase 2 (Devam Ediyor)
- Authentication (Supabase Auth)
- Tweet Generation (Claude AI)
- Tweet Analysis (Phoenix Score)
- Dashboard UI

### 🚀 Phase 3 (Planlandı)
- Tweet Scheduling
- A/B Testing System
- Analytics Dashboard

## 🔧 API Endpoints

### Tweets
- `POST /api/v1/tweets/generate` - AI ile tweet üret
- `POST /api/v1/tweets/analyze` - Tweet analizi
- `POST /api/v1/tweets/optimize` - Tweet optimize et
- `POST /api/v1/tweets/rewrite` - Yeniden yaz

### Profiles
- `GET /api/v1/profiles/me` - Profil bilgisi
- `POST /api/v1/profiles/analyze-style` - Stil analizi
- `GET /api/v1/profiles/tweetcred` - TweetCred skoru
- `GET /api/v1/profiles/monetization` - Para kazanma analizi

### Threads
- `POST /api/v1/threads/generate` - Thread üret
- `POST /api/v1/threads/from-tweet` - Tweet'ten thread'e çevir

### Scheduling
- `POST /api/v1/scheduling/schedule` - Tweet planla
- `GET /api/v1/scheduling/upcoming` - Gelecek tweetler
- `DELETE /api/v1/scheduling/:id` - İptal et

### A/B Testing
- `POST /api/v1/ab/campaigns` - Kampanya oluştur
- `GET /api/v1/ab/campaigns` - Kampanyalar
- `GET /api/v1/ab/campaigns/:id/results` - Sonuçlar

### Analytics
- `GET /api/v1/analytics/overview` - Genel istatistikler
- `GET /api/v1/analytics/performance` - Performans grafiği

## 📝 Lisans

MIT License

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Pull Request

---

**Not:** Bu proje X'in açık kaynak algoritma bilgilerine dayanır. Gerçek algoritma ağırlıkları gizlidir.
