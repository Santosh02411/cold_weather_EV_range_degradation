# Deployment Guide

This guide covers deploying the Unified Social Media Ads SaaS Platform to Cloudflare's edge computing platform.

## Prerequisites

- Node.js 18+ installed
- Cloudflare account with Workers, D1, KV, R2, and Queues enabled
- Cloudflare CLI (wrangler) installed
- Git installed

## Architecture Overview

The platform consists of:
- **Backend**: Cloudflare Workers with Hono framework
- **Frontend**: Next.js 14 (deployed separately or on Cloudflare Pages)
- **Database**: Cloudflare D1 (SQLite)
- **Storage**: Cloudflare R2 (media files)
- **Cache**: Cloudflare KV (sessions + tokens)
- **Queue**: Cloudflare Queues (async job processing)
- **State**: Cloudflare Durable Objects (campaign orchestration)

## Step 1: Backend Deployment

### 1.1 Install Dependencies

```bash
cd backend
npm install
```

### 1.2 Configure Cloudflare

Create a `wrangler.toml` file (already included) and update with your values:

```toml
name = "ads-saas-backend"
main = "src/index.js"
compatibility_date = "2024-04-01"

# D1 Database
[[d1_databases]]
binding = "DB"
database_name = "ads-saas-db"
database_id = "your-database-id"

# KV Storage
[[kv_namespaces]]
binding = "SESSIONS"
id = "your-sessions-kv-id"

[[kv_namespaces]]
binding = "TOKENS"
id = "your-tokens-kv-id"

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
JWT_SECRET = "your-jwt-secret-key"
ENVIRONMENT = "production"
```

### 1.3 Create Cloudflare Resources

#### Create D1 Database

```bash
# Create database
wrangler d1 create ads-saas-db

# Note the database_id and update wrangler.toml
```

#### Create KV Namespaces

```bash
# Create sessions KV
wrangler kv:namespace create "SESSIONS"

# Create tokens KV
wrangler kv:namespace create "TOKENS"

# Note the IDs and update wrangler.toml
```

#### Create R2 Bucket

```bash
# Create R2 bucket
wrangler r2 bucket create ads-saas-media
```

#### Create Queue

```bash
# Create queue (via Cloudflare Dashboard or API)
# Navigate to Cloudflare Dashboard > Workers & Pages > Queues
# Create queue named "campaign-jobs"
```

### 1.4 Run Database Migrations

```bash
# Apply migrations to production database
wrangler d1 migrations apply ads-saas-db

# For local development
wrangler d1 migrations apply ads-saas-db --local
```

### 1.5 Deploy Backend

```bash
# Deploy to Cloudflare Workers
wrangler deploy

# Test deployment
curl https://ads-saas-backend.your-subdomain.workers.dev/health
```

## Step 2: Frontend Deployment

### 2.1 Install Dependencies

```bash
cd frontend
npm install
```

### 2.2 Configure Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=https://ads-saas-backend.your-subdomain.workers.dev
```

### 2.3 Build and Deploy

#### Option A: Cloudflare Pages (Recommended)

```bash
# Build the application
npm run build

# Deploy to Cloudflare Pages
# Connect your GitHub repository to Cloudflare Pages
# Set build command: npm run build
# Set output directory: .next
```

#### Option B: Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

#### Option C: Netlify

```bash
# Build
npm run build

# Deploy to Netlify
# Connect repository and set build command
```

## Step 3: Post-Deployment Configuration

### 3.1 Update CORS Settings

In `backend/src/index.js`, update the CORS origins:

```javascript
app.use('*', cors({
  origin: ['https://your-frontend-domain.com', 'https://your-frontend-domain.pages.dev'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));
```

### 3.2 Set Environment Variables

#### Backend Variables

Update `wrangler.toml` with production values:

```toml
[vars]
JWT_SECRET = "your-secure-jwt-secret"
ENVIRONMENT = "production"
```

#### Frontend Variables

Set in your hosting platform:

```env
NEXT_PUBLIC_API_URL=https://ads-saas-backend.your-subdomain.workers.dev
```

### 3.3 Configure Custom Domains

#### Backend

```bash
# Add custom domain to Worker
wrangler custom-domains add api.your-domain.com
```

#### Frontend

Configure through your hosting provider's dashboard.

## Step 4: Testing the Deployment

### 4.1 Health Checks

```bash
# Backend health
curl https://api.your-domain.com/health

# Frontend accessibility
curl https://your-domain.com
```

### 4.2 API Testing

```bash
# Test registration
curl -X POST https://api.your-domain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Test login
curl -X POST https://api.your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### 4.3 Frontend Testing

1. Navigate to your frontend URL
2. Test user registration and login
3. Create a test campaign
4. Connect a platform (test credentials)
5. Test campaign publishing

## Step 5: Monitoring and Maintenance

### 5.1 Monitoring

#### Cloudflare Dashboard

- Monitor Worker metrics in Cloudflare Dashboard
- Check D1 database usage
- Monitor R2 storage costs
- Track Queue processing

#### Logs

```bash
# View real-time logs
wrangler tail

# View specific logs
wrangler tail --format=json
```

### 5.2 Database Maintenance

#### Backup Strategy

```bash
# Export D1 database
wrangler d1 export ads-saas-db --output=backup.sql

# Import D1 database (for recovery)
wrangler d1 import ads-saas-db --file=backup.sql
```

#### Performance Optimization

- Add indexes to frequently queried columns
- Monitor query performance
- Clean up old logs periodically

### 5.3 Security

#### Update Secrets Regularly

```bash
# Generate new JWT secret
openssl rand -base64 32

# Update wrangler.toml and redeploy
wrangler deploy
```

#### Rate Limiting

Consider implementing rate limiting in production:

```javascript
// Add to middleware
app.use('*', async (c, next) => {
  const clientIP = c.req.header('CF-Connecting-IP');
  // Implement rate limiting logic
  await next();
});
```

## Step 6: Scaling Considerations

### 6.1 Worker Scaling

- Cloudflare Workers auto-scale globally
- Monitor CPU time usage (50ms limit per request)
- Consider splitting heavy operations into multiple Workers

### 6.2 Database Scaling

- D1 handles up to 25,000 writes per second
- Consider read replicas for high-traffic applications
- Implement caching strategies with KV

### 6.3 Queue Scaling

- Queues handle millions of messages per day
- Monitor backlog and processing times
- Consider dead-letter queues for failed jobs

## Troubleshooting

### Common Issues

#### 1. CORS Errors

```javascript
// Ensure CORS is properly configured
app.use('*', cors({
  origin: true, // Be specific in production
  credentials: true
}));
```

#### 2. Database Connection Issues

```bash
# Check D1 binding
wrangler d1 list

# Verify database ID matches wrangler.toml
```

#### 3. Queue Processing Issues

```bash
# Check queue configuration
wrangler queues list

# Monitor queue metrics in dashboard
```

#### 4. Frontend Build Issues

```bash
# Clear Next.js cache
rm -rf .next

# Rebuild
npm run build
```

### Debug Mode

```bash
# Run backend locally
wrangler dev

# Run frontend locally
npm run dev
```

## Production Checklist

- [ ] All environment variables set
- [ ] Database migrations applied
- [ ] CORS configured for frontend domain
- [ ] Custom domains configured
- [ ] SSL certificates active
- [ ] Monitoring enabled
- [ ] Backup strategy in place
- [ ] Rate limiting implemented
- [ ] Error logging configured
- [ ] Health checks passing
- [ ] User testing completed
- [ ] Documentation updated

## Support and Resources

- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
- [Cloudflare D1 Documentation](https://developers.cloudflare.com/d1/)
- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Hono Documentation](https://hono.dev/)

## Cost Estimation

### Cloudflare Services (Free Tier Limits)

- **Workers**: 100,000 requests/day free
- **D1**: 5GB storage, 25M reads/day free
- **KV**: 100,000 reads/day, 1,000 writes/day free
- **R2**: 10GB storage free
- **Queues**: 1M messages/day free

### Estimated Monthly Costs (Beyond Free Tier)

- **Workers**: $0.50 per million requests
- **D1**: $0.75 per million reads, $5 per million writes
- **KV**: $0.50 per million reads, $5 per million writes
- **R2**: $0.015 per GB stored + $0.01 per GB downloaded
- **Queues**: $0.40 per million messages

For a small to medium application, expect costs under $50/month initially.
