import { Hono } from 'hono';
import { cors } from 'hono/cors';

const app = new Hono();

// Middleware
app.use('*', cors({
  origin: ['http://localhost:3000'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));

// Health check
app.get('/health', (c) => {
  return c.json({ status: 'ok', timestamp: new Date().toISOString() });
});


// Simple auth routes
app.post('/api/auth/register', async (c) => {
  const { email, password } = await c.req.json();
  
  // Check if user already exists
  if (users.has(email)) {
    return c.json({ error: 'User already exists' }, 400);
  }
  
  // Create new user
  const user = { 
    id: Date.now().toString(), 
    email,
    created_at: new Date().toISOString()
  };
  
  // Store user (in real app, would hash password)
  users.set(email, { ...user, password });
  
  const token = 'mock-jwt-token-' + Date.now();
  
  return c.json({ user, token });
});

app.post('/api/auth/login', async (c) => {
  const { email, password } = await c.req.json();
  
  // Check if user exists
  const storedUser = users.get(email);
  if (!storedUser) {
    return c.json({ error: 'Invalid credentials' }, 401);
  }
  
  // Check password (in real app, would compare hashed passwords)
  if (storedUser.password !== password) {
    return c.json({ error: 'Invalid credentials' }, 401);
  }
  
  const user = { 
    id: storedUser.id, 
    email: storedUser.email,
    created_at: storedUser.created_at
  };
  
  const token = 'mock-jwt-token-' + Date.now();
  
  return c.json({ user, token });
});

app.get('/api/auth/me', (c) => {
  return c.json({ user: { id: '1', email: 'test@example.com' } });
});

// Simple in-memory storage with KV persistence for demo
const campaigns = new Map();
const platforms = new Map();
const mediaFiles = new Map();
const users = new Map();

// Initialize with some default platforms
platforms.set('1', { id: '1', name: 'Facebook', type: 'facebook', is_connected: false, user_id: '1' });
platforms.set('2', { id: '2', name: 'Google', type: 'google', is_connected: false, user_id: '1' });
platforms.set('3', { id: '3', name: 'TikTok', type: 'tiktok', is_connected: false, user_id: '1' });
platforms.set('4', { id: '4', name: 'Instagram', type: 'instagram', is_connected: false, user_id: '1' });

// Campaigns endpoints
app.get('/api/campaigns', (c) => {
  const campaignList = campaigns.values();
  return c.json({ campaigns: campaignList });
});

app.post('/api/campaigns', async (c) => {
  const campaignData = await c.req.json();
  const campaign = {
    id: Date.now().toString(),
    title: campaignData.title,
    description: campaignData.description || '',
    budget: campaignData.budget,
    status: 'draft',
    platforms: campaignData.platforms || [],
    schedule_start: campaignData.scheduleStart,
    schedule_end: campaignData.scheduleEnd,
    user_id: '1',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
  
  campaigns.set(campaign.id, campaign);
  return c.json({ campaign }, 201);
});

app.post('/api/campaigns/:id/publish', async (c) => {
  const id = c.req.param('id');
  const campaign = campaigns.get(id);
  
  if (!campaign) {
    return c.json({ error: 'Campaign not found' }, 404);
  }
  
  campaign.status = 'active';
  campaign.updated_at = new Date().toISOString();
  
  return c.json({ campaign });
});

app.delete('/api/campaigns/:id', (c) => {
  const id = c.req.param('id');
  const deleted = campaigns.delete(id);
  
  if (!deleted) {
    return c.json({ error: 'Campaign not found' }, 404);
  }
  
  return c.json({ message: 'Campaign deleted successfully' });
});

// Platforms endpoints
app.get('/api/platforms', (c) => {
  const platformList = platforms.values();
  return c.json({ platforms: platformList });
});

app.get('/api/platforms/connected', (c) => {
  const connectedPlatforms = platforms.values().filter(p => p.is_connected);
  return c.json({ platforms: connectedPlatforms });
});

app.post('/api/platforms/:id/connect', async (c) => {
  const id = c.req.param('id');
  const platform = platforms.get(id);
  
  if (!platform) {
    return c.json({ error: 'Platform not found' }, 404);
  }
  
  platform.is_connected = true;
  platform.config = { connected: true };
  
  return c.json({ platform });
});

app.post('/api/platforms/:id/disconnect', async (c) => {
  const id = c.req.param('id');
  const platform = platforms.get(id);
  
  if (!platform) {
    return c.json({ error: 'Platform not found' }, 404);
  }
  
  platform.is_connected = false;
  platform.config = {};
  
  return c.json({ platform });
});

app.delete('/api/platforms/:id', (c) => {
  const id = c.req.param('id');
  const deleted = platforms.delete(id);
  
  if (!deleted) {
    return c.json({ error: 'Platform not found' }, 404);
  }
  
  return c.json({ message: 'Platform deleted successfully' });
});

// Media endpoints
app.get('/api/media', (c) => {
  const mediaList = mediaFiles.values();
  return c.json({ media: mediaList });
});

app.post('/api/media/upload', async (c) => {
  const uploadData = await c.req.json();
  
  // Create media record
  const media = {
    id: Date.now().toString(),
    filename: uploadData.filename || `media-${Date.now()}.jpg`,
    original_name: uploadData.original_name || uploadData.filename || 'Uploaded Media',
    mime_type: uploadData.mime_type || 'image/jpeg',
    size: uploadData.size || 1024,
    url: `https://via.placeholder.com/400x300?text=${encodeURIComponent(uploadData.original_name || 'Media')}`,
    user_id: '1',
    created_at: new Date().toISOString()
  };
  
  // Store in memory
  mediaFiles.set(media.id, media);
  
  return c.json({ media }, 201);
});

app.delete('/api/media/:id', (c) => {
  const id = c.req.param('id');
  const deleted = mediaFiles.delete(id);
  
  if (!deleted) {
    return c.json({ error: 'Media not found' }, 404);
  }
  
  return c.json({ message: 'Media deleted successfully' });
});

// Status endpoints
app.get('/api/status/overview', (c) => {
  const campaignList = campaigns.values();
  const platformList = platforms.values();
  
  return c.json({
    campaigns: {
      total_campaigns: campaignList.length,
      active_campaigns: campaignList.filter(c => c.status === 'active').length,
      draft_campaigns: campaignList.filter(c => c.status === 'draft').length,
      paused_campaigns: campaignList.filter(c => c.status === 'paused').length,
      completed_campaigns: campaignList.filter(c => c.status === 'completed').length,
      total_budget: campaignList.reduce((sum, c) => sum + c.budget, 0)
    },
    platforms: {
      total_platforms: platformList.length,
      connected_platforms: platformList.filter(p => p.is_connected).length,
      disconnected_platforms: platformList.filter(p => !p.is_connected).length
    },
    jobs: {
      total_jobs: 0,
      pending_jobs: 0,
      processing_jobs: 0,
      success_jobs: 0,
      failed_jobs: 0
    },
    recentActivity: []
  });
});

export default {
  fetch: app.fetch
};
