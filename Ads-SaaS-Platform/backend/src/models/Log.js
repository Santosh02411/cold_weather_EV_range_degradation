// Removed uuid import

export class Log {
  constructor(db) {
    this.db = db;
  }

  async create(logData) {
    const { level, message, context, userId, campaignId, platformId } = logData;
    const logId = crypto.randomUUID();

    const stmt = this.db.prepare(`
      INSERT INTO logs (id, level, message, context, user_id, campaign_id, platform_id)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    await stmt.bind(
      logId,
      level || 'info',
      message || '',
      context ? JSON.stringify(context) : null,
      userId || null,
      campaignId || null,
      platformId || null
    ).run();

    return this.findById(logId);
  }

  async findById(logId) {
    const stmt = this.db.prepare(`
      SELECT id, level, message, context, user_id, campaign_id, platform_id, created_at
      FROM logs WHERE id = ?
    `);

    const result = await stmt.bind(logId).first();
    
    if (result && result.context) {
      result.context = JSON.parse(result.context);
    }
    
    return result;
  }

  async findByUserId(userId, limit = 100, offset = 0, level = null) {
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
    
    query += ` ORDER BY created_at DESC LIMIT ? OFFSET ?`;
    params.push(limit, offset);

    const stmt = this.db.prepare(query);
    const results = await stmt.bind(...params).all();
    
    return results.map(log => ({
      ...log,
      context: log.context ? JSON.parse(log.context) : {}
    }));
  }

  async findByCampaignId(campaignId, limit = 50) {
    const stmt = this.db.prepare(`
      SELECT id, level, message, context, user_id, platform_id, created_at
      FROM logs 
      WHERE campaign_id = ?
      ORDER BY created_at DESC
      LIMIT ?
    `);

    const results = await stmt.bind(campaignId, limit).all();
    
    return results.map(log => ({
      ...log,
      context: log.context ? JSON.parse(log.context) : {}
    }));
  }

  async findByPlatformId(platformId, limit = 50) {
    const stmt = this.db.prepare(`
      SELECT id, level, message, context, user_id, campaign_id, created_at
      FROM logs 
      WHERE platform_id = ?
      ORDER BY created_at DESC
      LIMIT ?
    `);

    const results = await stmt.bind(platformId, limit).all();
    
    return results.map(log => ({
      ...log,
      context: log.context ? JSON.parse(log.context) : {}
    }));
  }

  async getLogStats(userId, timeRange = '24h') {
    let timeFilter = '';
    if (timeRange === '24h') {
      timeFilter = "AND created_at >= datetime('now', '-1 day')";
    } else if (timeRange === '7d') {
      timeFilter = "AND created_at >= datetime('now', '-7 days')";
    } else if (timeRange === '30d') {
      timeFilter = "AND created_at >= datetime('now', '-30 days')";
    }

    const stmt = this.db.prepare(`
      SELECT 
        COUNT(*) as total_logs,
        COUNT(CASE WHEN level = 'error' THEN 1 END) as error_count,
        COUNT(CASE WHEN level = 'warn' THEN 1 END) as warn_count,
        COUNT(CASE WHEN level = 'info' THEN 1 END) as info_count,
        COUNT(CASE WHEN level = 'debug' THEN 1 END) as debug_count
      FROM logs 
      WHERE user_id = ? ${timeFilter}
    `);

    return await stmt.bind(userId).first();
  }

  async getRecentLogs(userId, limit = 10) {
    const stmt = this.db.prepare(`
      SELECT id, level, message, campaign_id, platform_id, created_at
      FROM logs 
      WHERE user_id = ?
      ORDER BY created_at DESC
      LIMIT ?
    `);

    return await stmt.bind(userId, limit).all();
  }

  async deleteOldLogs(daysOld = 30) {
    const stmt = this.db.prepare(`
      DELETE FROM logs 
      WHERE created_at < datetime('now', '-${daysOld} days')
    `);

    return await stmt.run();
  }

  async cleanup(userId, maxLogs = 1000) {
    // Keep only the most recent logs for a user
    const stmt = this.db.prepare(`
      DELETE FROM logs 
      WHERE user_id = ? AND id NOT IN (
        SELECT id FROM logs 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
      )
    `);

    return await stmt.bind(userId, userId, maxLogs).run();
  }

  // Convenience methods for different log levels
  async info(message, context = {}, userId = null, campaignId = null, platformId = null) {
    return await this.create({
      level: 'info',
      message,
      context,
      userId,
      campaignId,
      platformId
    });
  }

  async warn(message, context = {}, userId = null, campaignId = null, platformId = null) {
    return await this.create({
      level: 'warn',
      message,
      context,
      userId,
      campaignId,
      platformId
    });
  }

  async error(message, context = {}, userId = null, campaignId = null, platformId = null) {
    return await this.create({
      level: 'error',
      message,
      context,
      userId,
      campaignId,
      platformId
    });
  }

  async debug(message, context = {}, userId = null, campaignId = null, platformId = null) {
    return await this.create({
      level: 'debug',
      message,
      context,
      userId,
      campaignId,
      platformId
    });
  }
}
