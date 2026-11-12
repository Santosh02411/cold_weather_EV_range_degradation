import { Hono } from 'hono';
import { Log } from '../models/Log.js';
import { Campaign } from '../models/Campaign.js';

const status = new Hono();

// Get overall status for user
status.get('/overview', async (c) => {
  try {
    const userId = c.get('userId');

    // Get campaign stats
    const campaignStats = await c.env.DB.prepare(`
      SELECT 
        COUNT(*) as total_campaigns,
        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_campaigns,
        COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_campaigns,
        COUNT(CASE WHEN status = 'paused' THEN 1 END) as paused_campaigns,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_campaigns,
        SUM(budget) as total_budget
      FROM campaigns 
      WHERE user_id = ?
    `).bind(userId).first();

    // Get platform status
    const platformStats = await c.env.DB.prepare(`
      SELECT 
        COUNT(*) as total_platforms,
        COUNT(CASE WHEN is_connected = TRUE THEN 1 END) as connected_platforms,
        COUNT(CASE WHEN is_connected = FALSE THEN 1 END) as disconnected_platforms
      FROM platforms 
      WHERE user_id = ?
    `).bind(userId).first();

    // Get job status
    const jobStats = await c.env.DB.prepare(`
      SELECT 
        COUNT(*) as total_jobs,
        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_jobs,
        COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_jobs,
        COUNT(CASE WHEN status = 'success' THEN 1 END) as success_jobs,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs
      FROM jobs j
      JOIN campaigns c ON j.campaign_id = c.id
      WHERE c.user_id = ?
    `).bind(userId).first();

    // Get recent activity
    const recentLogs = await c.env.DB.prepare(`
      SELECT level, message, campaign_id, platform_id, created_at
      FROM logs 
      WHERE user_id = ?
      ORDER BY created_at DESC
      LIMIT 10
    `).bind(userId).all();

    return c.json({
      campaigns: campaignStats,
      platforms: platformStats,
      jobs: jobStats,
      recentActivity: recentLogs
    });
  } catch (error) {
    console.error('Get status overview error:', error);
    return c.json({ error: 'Failed to get status overview' }, 500);
  }
});

// Get campaign status
status.get('/campaigns/:id', async (c) => {
  try {
    const userId = c.get('userId');
    const campaignId = c.req.param('id');

    // Verify campaign ownership
    const campaign = new Campaign(c.env.DB);
    const campaignData = await campaign.findById(campaignId);

    if (!campaignData) {
      return c.json({ error: 'Campaign not found' }, 404);
    }

    if (campaignData.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    // Get platform-specific status
    const platformStatus = await c.env.DB.prepare(`
      SELECT 
        cp.id,
        cp.platform_id,
        p.name as platform_name,
        p.type as platform_type,
        cp.status,
        cp.error_message,
        cp.retry_count,
        cp.created_at,
        cp.updated_at
      FROM campaign_platforms cp
      JOIN platforms p ON cp.platform_id = p.id
      WHERE cp.campaign_id = ?
      ORDER BY cp.created_at DESC
    `).bind(campaignId).all();

    // Get job history
    const jobHistory = await c.env.DB.prepare(`
      SELECT 
        id,
        action,
        status,
        error_message,
        retry_count,
        scheduled_at,
        processed_at,
        created_at
      FROM jobs
      WHERE campaign_id = ?
      ORDER BY created_at DESC
      LIMIT 20
    `).bind(campaignId).all();

    // Get recent logs
    const recentLogs = await c.env.DB.prepare(`
      SELECT level, message, context, created_at
      FROM logs 
      WHERE campaign_id = ?
      ORDER BY created_at DESC
      LIMIT 10
    `).bind(campaignId).all();

    return c.json({
      campaign: campaignData,
      platformStatus,
      jobHistory,
      recentLogs
    });
  } catch (error) {
    console.error('Get campaign status error:', error);
    return c.json({ error: 'Failed to get campaign status' }, 500);
  }
});

// Get platform status
status.get('/platforms/:id', async (c) => {
  try {
    const userId = c.get('userId');
    const platformId = c.req.param('id');

    // Verify platform ownership
    const platform = await c.env.DB.prepare(`
      SELECT id, name, type, is_connected, created_at
      FROM platforms 
      WHERE id = ? AND user_id = ?
    `).bind(platformId, userId).first();

    if (!platform) {
      return c.json({ error: 'Platform not found' }, 404);
    }

    // Get campaign performance on this platform
    const campaignPerformance = await c.env.DB.prepare(`
      SELECT 
        c.id,
        c.title,
        c.status as campaign_status,
        cp.status as platform_status,
        cp.error_message,
        cp.retry_count,
        cp.created_at
      FROM campaign_platforms cp
      JOIN campaigns c ON cp.campaign_id = c.id
      WHERE cp.platform_id = ?
      ORDER BY cp.created_at DESC
      LIMIT 20
    `).bind(platformId).all();

    // Get recent logs for this platform
    const recentLogs = await c.env.DB.prepare(`
      SELECT level, message, context, campaign_id, created_at
      FROM logs 
      WHERE platform_id = ?
      ORDER BY created_at DESC
      LIMIT 10
    `).bind(platformId).all();

    return c.json({
      platform,
      campaignPerformance,
      recentLogs
    });
  } catch (error) {
    console.error('Get platform status error:', error);
    return c.json({ error: 'Failed to get platform status' }, 500);
  }
});

// Get job status
status.get('/jobs', async (c) => {
  try {
    const userId = c.get('userId');
    const limit = parseInt(c.req.query('limit') || '50');
    const offset = parseInt(c.req.query('offset') || '0');
    const status = c.req.query('status');

    let query = `
      SELECT 
        j.id,
        j.campaign_id,
        j.platform_id,
        j.action,
        j.status,
        j.error_message,
        j.retry_count,
        j.scheduled_at,
        j.processed_at,
        j.created_at,
        c.title as campaign_title,
        p.name as platform_name
      FROM jobs j
      JOIN campaigns c ON j.campaign_id = c.id
      JOIN platforms p ON j.platform_id = p.id
      WHERE c.user_id = ?
    `;

    const params = [userId];

    if (status) {
      query += ` AND j.status = ?`;
      params.push(status);
    }

    query += ` ORDER BY j.created_at DESC LIMIT ? OFFSET ?`;
    params.push(limit, offset);

    const jobs = await c.env.DB.prepare(query).bind(...params).all();

    return c.json({ jobs });
  } catch (error) {
    console.error('Get jobs status error:', error);
    return c.json({ error: 'Failed to get jobs status' }, 500);
  }
});

// Get logs
status.get('/logs', async (c) => {
  try {
    const userId = c.get('userId');
    const limit = parseInt(c.req.query('limit') || '100');
    const offset = parseInt(c.req.query('offset') || '0');
    const level = c.req.query('level');
    const campaignId = c.req.query('campaignId');
    const platformId = c.req.query('platformId');

    let query = `
      SELECT id, level, message, context, campaign_id, platform_id, created_at
      FROM logs 
      WHERE user_id = ?
    `;

    const params = [userId];

    if (level) {
      query += ` AND level = ?`;
      params.push(level);
    }

    if (campaignId) {
      query += ` AND campaign_id = ?`;
      params.push(campaignId);
    }

    if (platformId) {
      query += ` AND platform_id = ?`;
      params.push(platformId);
    }

    query += ` ORDER BY created_at DESC LIMIT ? OFFSET ?`;
    params.push(limit, offset);

    const logs = await c.env.DB.prepare(query).bind(...params).all();

    // Parse context for each log
    const parsedLogs = logs.map(log => ({
      ...log,
      context: log.context ? JSON.parse(log.context) : {}
    }));

    return c.json({ logs: parsedLogs });
  } catch (error) {
    console.error('Get logs error:', error);
    return c.json({ error: 'Failed to get logs' }, 500);
  }
});

// Retry failed job
status.post('/jobs/:id/retry', async (c) => {
  try {
    const userId = c.get('userId');
    const jobId = c.req.param('id');

    // Verify job ownership
    const job = await c.env.DB.prepare(`
      SELECT j.*, c.user_id
      FROM jobs j
      JOIN campaigns c ON j.campaign_id = c.id
      WHERE j.id = ?
    `).bind(jobId).first();

    if (!job) {
      return c.json({ error: 'Job not found' }, 404);
    }

    if (job.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    if (job.status !== 'failed') {
      return c.json({ error: 'Only failed jobs can be retried' }, 400);
    }

    // Update job status
    await c.env.DB.prepare(`
      UPDATE jobs 
      SET status = 'pending', 
          retry_count = retry_count + 1,
          error_message = NULL,
          updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `).bind(jobId).run();

    // Resend to queue
    const jobData = {
      campaignId: job.campaign_id,
      platformId: job.platform_id,
      action: job.action,
      payload: JSON.parse(job.payload || '{}')
    };

    await c.env.CAMPAIGN_QUEUE.send(JSON.stringify(jobData));

    const log = new Log(c.env.DB);
    await log.info('Job retried', { 
      jobId: jobId,
      retryCount: job.retry_count + 1
    }, userId, job.campaign_id, job.platform_id);

    return c.json({ message: 'Job retried successfully' });
  } catch (error) {
    console.error('Retry job error:', error);
    return c.json({ error: 'Failed to retry job' }, 500);
  }
});

// Get system health
status.get('/health', async (c) => {
  try {
    // Check database connection
    const dbCheck = await c.env.DB.prepare('SELECT 1 as test').first();

    // Check KV connection
    let kvCheck = false;
    try {
      await c.env.SESSIONS.put('health-check', 'ok', { expirationTtl: 60 });
      const value = await c.env.SESSIONS.get('health-check');
      kvCheck = value === 'ok';
    } catch (error) {
      console.error('KV health check failed:', error);
    }

    // Check R2 connection
    let r2Check = false;
    try {
      const objects = await c.env.MEDIA_BUCKET.list({ limit: 1 });
      r2Check = true;
    } catch (error) {
      console.error('R2 health check failed:', error);
    }

    // Check Queue connection
    let queueCheck = false;
    try {
      // This is a basic check - in production you might want more sophisticated checks
      queueCheck = !!c.env.CAMPAIGN_QUEUE;
    } catch (error) {
      console.error('Queue health check failed:', error);
    }

    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        database: !!dbCheck,
        kv: kvCheck,
        r2: r2Check,
        queue: queueCheck
      }
    };

    const allHealthy = Object.values(health.services).every(status => status);
    health.status = allHealthy ? 'healthy' : 'degraded';

    return c.json(health);
  } catch (error) {
    console.error('Health check error:', error);
    return c.json({ 
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString()
    }, 500);
  }
});

export { status as statusRoutes };
