# Getting Started Guide

This guide will help you set up and run the Unified Social Media Ads SaaS Platform locally and in production.

## Prerequisites

- Node.js 18+ installed
- Cloudflare CLI (wrangler) installed
- Git installed
- Cloudflare account with Workers, D1, KV, R2, and Queues enabled

## Quick Start

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd ads-saas-platform

# Install backend dependencies
cd backend
npm install

# Install frontend dependencies
cd ../frontend
npm install
cd ..
```

### 2. Set Up Cloudflare Resources

#### Install Wrangler CLI
```bash
npm install -g wrangler
```

#### Authenticate with Cloudflare
```bash
wrangler auth login
```

#### Create D1 Database
```bash
# Create database
wrangler d1 create ads-saas-db

# Note the database_id and update backend/wrangler.toml
```

#### Create KV Namespaces
```bash
# Create sessions KV
wrangler kv:namespace create "SESSIONS"

# Create tokens KV
wrangler kv:namespace create "TOKENS"

# Note the IDs and update backend/wrangler.toml
```

#### Create R2 Bucket
```bash
# Create R2 bucket
wrangler r2 bucket create ads-saas-media
```

#### Create Queue
Navigate to [Cloudflare Dashboard](https://dash.cloudflare.com/) > Workers & Pages > Queues and create a queue named `campaign-jobs`.

### 3. Configure Environment

#### Backend Configuration

Update `backend/wrangler.toml` with your Cloudflare resource IDs:

```toml
name = "ads-saas-backend"
main = "src/index.js"
compatibility_date = "2024-04-01"

# D1 Database
[[d1_databases]]
binding = "DB"
database_name = "ads-saas-db"
database_id = "your-database-id-here"

# KV Storage
[[kv_namespaces]]
binding = "SESSIONS"
id = "your-sessions-kv-id-here"

[[kv_namespaces]]
binding = "TOKENS"
id = "your-tokens-kv-id-here"

# R2 Storage
[[r2_buckets]]
binding = "MEDIA_BUCKET"
bucket_name = "ads-saas-media"

# Queues
[[queues.producers]]
binding = "CAMPAIGN_QUEUE"
queue = "campaign-jobs"

[[queues.consumers]]
queue = "campaign-jobs"

# Durable Objects
[[durable_objects.bindings]]
name = "CAMPAIGN_ORCHESTRATOR"
class_name = "CampaignOrchestrator"

[vars]
JWT_SECRET = "your-secure-jwt-secret-key"
ENVIRONMENT = "development"
```

#### Frontend Configuration

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8787
```

### 4. Run Database Migrations

```bash
cd backend

# Apply migrations to local database
wrangler d1 migrations apply ads-saas-db --local

# For production
wrangler d1 migrations apply ads-saas-db
```

## Running Locally

### Option 1: Backend Only (for API testing)

```bash
cd backend

# Start local development server
wrangler dev

# The API will be available at http://localhost:8787
```

### Option 2: Full Stack (Recommended)

```bash
# Terminal 1: Start backend
cd backend
wrangler dev

# Terminal 2: Start frontend
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8787

## Testing the Application

### 1. Create an Account

1. Navigate to http://localhost:3000
2. Click "Sign up" and create an account
3. Verify you can log in successfully

### 2. Connect a Platform

1. Go to the "Integrations" page
2. Click "Connect" on any platform (Facebook, Google, TikTok, Instagram)
3. Enter test credentials (mock implementation accepts any values)
4. Verify the platform shows as "Connected"

### 3. Create a Campaign

1. Navigate to "Campaigns" page
2. Click "New Campaign"
3. Fill in campaign details:
   - Title: "Test Campaign"
   - Budget: 100
   - Select connected platforms
4. Click "Create Campaign"

### 4. Publish a Campaign

1. From the campaigns list, click the play icon on your campaign
2. Monitor the status in the "Status" page
3. Check the job processing and logs

### 5. Test API Endpoints

```bash
# Health check
curl http://localhost:8787/health

# Register user
curl -X POST http://localhost:8787/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:8787/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

## Development Workflow

### Making Changes

1. **Backend Changes**: Edit files in `backend/src/`
2. **Frontend Changes**: Edit files in `frontend/src/`
3. **Database Changes**: Create new migration files in `database/migrations/`

### Hot Reloading

- Backend: `wrangler dev` automatically reloads on changes
- Frontend: Next.js dev server automatically reloads on changes

### Debugging

#### Backend Debugging
```bash
# Enable verbose logging
wrangler dev --log-level debug

# View logs in real-time
wrangler tail
```

#### Frontend Debugging
- Open browser developer tools
- Check Network tab for API calls
- Console for JavaScript errors

### Database Management

#### Adding New Tables
```bash
# Create new migration
wrangler d1 migrations create ads-saas-db new_table_name

# Edit the generated SQL file
# Apply migration
wrangler d1 migrations apply ads-saas-db --local
```

#### Local Database Access
```bash
# Execute SQL directly
wrangler d1 execute ads-saas-db --local --command "SELECT * FROM users"
```

## Production Deployment

### 1. Deploy Backend

```bash
cd backend

# Deploy to Cloudflare Workers
wrangler deploy

# Test production endpoint
curl https://ads-saas-backend.your-subdomain.workers.dev/health
```

### 2. Deploy Frontend

#### Cloudflare Pages (Recommended)
1. Connect your GitHub repository to Cloudflare Pages
2. Set build command: `npm run build`
3. Set output directory: `.next`
4. Deploy automatically on push to main branch

#### Vercel
```bash
cd frontend
npm install -g vercel
vercel --prod
```

### 3. Update Production Configuration

#### Backend
Update `wrangler.toml` with production values:
```toml
[vars]
JWT_SECRET = "your-production-jwt-secret"
ENVIRONMENT = "production"
```

#### Frontend
Set environment variables in your hosting platform:
```env
NEXT_PUBLIC_API_URL=https://ads-saas-backend.your-subdomain.workers.dev
```

### 4. Production Testing

1. Test user registration and login
2. Test campaign creation and publishing
3. Verify platform integrations work
4. Check status monitoring and logs

## Troubleshooting

### Common Issues

#### 1. "Module not found" errors
```bash
# Clear npm cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

#### 2. Database connection errors
```bash
# Verify database ID in wrangler.toml
wrangler d1 list

# Re-run migrations
wrangler d1 migrations apply ads-saas-db --local
```

#### 3. CORS errors
Update CORS configuration in `backend/src/index.js`:
```javascript
app.use('*', cors({
  origin: ['http://localhost:3000'], // Add your frontend URL
  credentials: true
}));
```

#### 4. Queue processing issues
```bash
# Check queue configuration in Cloudflare Dashboard
# Verify queue binding in wrangler.toml
```

### Getting Help

1. Check the [troubleshooting guide](docs/troubleshooting.md)
2. Review [API documentation](docs/api-documentation.md)
3. Check Cloudflare Workers documentation
4. Review error logs in the dashboard

## Development Tips

### 1. Use Mock Data
The platform includes mock implementations for all platform APIs, so you can test without real credentials.

### 2. Monitor Resource Usage
- Check Cloudflare dashboard for usage metrics
- Monitor D1 database queries
- Track Worker CPU time usage

### 3. Test Error Scenarios
- Test failed job processing
- Test platform disconnection
- Test network timeouts

### 4. Performance Optimization
- Add database indexes for frequently queried columns
- Implement caching for expensive operations
- Monitor and optimize Worker CPU time

## Next Steps

1. **Explore the Code**: Read through the source code to understand the architecture
2. **Add Features**: Implement new platforms or features using the modular adapter system
3. **Customize UI**: Modify the frontend to match your brand
4. **Scale Up**: Monitor usage and upgrade Cloudflare plans as needed

## Support

For additional help:
- Review the comprehensive [documentation](docs/)
- Check the [deployment guide](docs/deployment.md)
- Refer to [Cloudflare documentation](https://developers.cloudflare.com/)
- Open an issue in the project repository
