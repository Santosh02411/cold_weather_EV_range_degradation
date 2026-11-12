import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { authRoutes } from './routes/auth.js';
import { campaignRoutes } from './routes/campaigns.js';
import { platformRoutes } from './routes/platforms.js';
import { mediaRoutes } from './routes/media.js';
import { statusRoutes } from './routes/status.js';
import { errorHandler } from './middleware/errorHandler.js';
import { authMiddleware } from './middleware/auth.js';
import { CampaignOrchestrator } from './durable-objects/CampaignOrchestrator.js';

const app = new Hono();

// Middleware
app.use('*', cors({
  origin: ['http://localhost:3000', 'https://your-frontend-domain.com'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));

app.use('*', logger());
app.use('*', errorHandler);

// Public routes
app.route('/api/auth', authRoutes);
app.get('/health', (c) => {
  return c.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Protected routes middleware
app.use('/api/*', authMiddleware);

// Protected routes
app.route('/api/platforms', platformRoutes);
app.route('/api/campaigns', campaignRoutes);
app.route('/api/media', mediaRoutes);
app.route('/api/status', statusRoutes);

// 404 handler
app.notFound((c) => {
  return c.json({ error: 'Not Found' }, 404);
});

export default {
  fetch: app.fetch,
  queue: async (batch, env) => {
    // Handle queue messages for campaign processing
    for (const message of batch.messages) {
      const { campaignId, platform, action } = JSON.parse(message.body);
      
      // Process the campaign job
      try {
        // This will be implemented in the queue worker
        console.log(`Processing campaign ${campaignId} for platform ${platform}`);
        message.ack();
      } catch (error) {
        console.error(`Failed to process campaign ${campaignId}:`, error);
        message.retry();
      }
    }
  }
};

export { CampaignOrchestrator };
