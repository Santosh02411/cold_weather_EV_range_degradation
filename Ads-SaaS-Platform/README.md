# Unified Social Media Ads SaaS Platform

A production-ready MVP for managing social media advertising campaigns across multiple platforms.

## Architecture

- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + TypeScript
- **Backend**: Cloudflare Workers + Hono framework
- **Database**: Cloudflare D1 (SQLite)
- **Storage**: Cloudflare R2 (media files)
- **Cache**: Cloudflare KV (sessions + tokens)
- **Queues**: Cloudflare Queues (async job processing)
- **State Management**: Cloudflare Durable Objects (campaign orchestration)

## Features

- Multi-platform ad management (Facebook, Google, TikTok, Instagram)
- Campaign creation and scheduling
- Media upload and management
- Real-time status tracking
- AI-powered ad copy generation
- Retry mechanisms for failed jobs
- Campaign duplication

## Project Structure

```
ads-saas-platform/
├── backend/                 # Cloudflare Workers + Hono
│   └── src/
│       ├── adapters/        # Platform integration modules
│       ├── durable-objects/ # Campaign orchestration
│       ├── middleware/      # Auth and validation
│       ├── models/          # Data models
│       ├── routes/          # API endpoints
│       ├── services/        # Business logic
│       ├── utils/           # Helper functions
│       └── workers/         # Queue processors
├── frontend/                # Next.js application
│   └── src/
│       ├── app/            # App Router pages
│       ├── components/     # Reusable UI components
│       ├── hooks/          # Custom React hooks
│       ├── lib/            # Utility libraries
│       ├── types/          # TypeScript definitions
│       └── utils/          # Helper functions
├── database/
│   └── migrations/         # D1 database migrations
├── docs/                   # Documentation
└── scripts/               # Deployment and utility scripts
```

## Getting Started

### Prerequisites

- **Node.js**: Version 18 or higher
- **Cloudflare CLI (Wrangler)**: Installed globally (`npm install -g wrangler`)
- **Git**: For version control

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ads-saas-platform
   ```

2. **Set up the Backend**:
   ```bash
   cd backend
   npm install
   ```

3. **Set up the Frontend**:
   ```bash
   cd ../frontend
   npm install
   ```

### Configuration

#### 1. Backend (Cloudflare)
Update `backend/wrangler.toml` with your Cloudflare resource IDs. You'll need to create:
- A D1 database: `wrangler d1 create ads-saas-db`
- KV namespaces: `wrangler kv:namespace create "SESSIONS"` and `wrangler kv:namespace create "TOKENS"`
- An R2 bucket: `wrangler r2 bucket create ads-saas-media`

#### 2. Frontend
Create a `.env.local` file in the `frontend` directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8787
```

## Running Locally

To run the full stack locally:

1. **Start the Backend**:
   ```bash
   cd backend
   wrangler dev
   ```
   The API will be available at `http://localhost:8787`.

2. **Start the Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   The application will be available at `http://localhost:3000`.

## Testing the API

You can perform a quick health check on the backend:
```bash
curl http://localhost:8787/health
```

## Deployment

The platform is designed for Cloudflare's edge computing platform.

1. **Deploy Backend**:
   ```bash
   cd backend
   wrangler deploy
   ```

2. **Deploy Frontend**:
   Deploy to Cloudflare Pages or Vercel. For Cloudflare Pages, use `npm run build` as the build command and `.next` as the output directory.

## License

MIT License
