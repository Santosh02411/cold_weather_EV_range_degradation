import { v4 as uuidv4 } from 'uuid';

export class Campaign {
  constructor(db) {
    this.db = db;
  }

  async create(campaignData, userId) {
    const {
      title,
      description,
      budget,
      scheduleStart,
      scheduleEnd,
      platforms
    } = campaignData;

    const campaignId = uuidv4();

    // Create campaign
    const stmt = this.db.prepare(`
      INSERT INTO campaigns (id, title, description, budget, schedule_start, schedule_end, user_id)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    await stmt.bind(
      campaignId,
      title,
      description,
      budget,
      scheduleStart,
      scheduleEnd,
      userId
    ).run();

    // Link platforms to campaign
    if (platforms && platforms.length > 0) {
      await this.linkPlatforms(campaignId, platforms);
    }

    return this.findById(campaignId);
  }

  async findById(campaignId) {
    const stmt = this.db.prepare(`
      SELECT c.*, 
             json_group_array(
               json_object(
                 'id', cp.id,
                 'platformId', cp.platform_id,
                 'platformName', p.name,
                 'platformType', p.type,
                 'status', cp.status,
                 'errorMessage', cp.error_message,
                 'retryCount', cp.retry_count
               )
             ) as platforms
      FROM campaigns c
      LEFT JOIN campaign_platforms cp ON c.id = cp.campaign_id
      LEFT JOIN platforms p ON cp.platform_id = p.id
      WHERE c.id = ?
      GROUP BY c.id
    `);

    const result = await stmt.bind(campaignId).first();
    
    if (result && result.platforms) {
      result.platforms = JSON.parse(result.platforms);
    }
    
    return result;
  }

  async findByUserId(userId, limit = 50, offset = 0) {
    const stmt = this.db.prepare(`
      SELECT c.*, 
             COUNT(cp.id) as platform_count,
             SUM(CASE WHEN cp.status = 'success' THEN 1 ELSE 0 END) as success_count,
             SUM(CASE WHEN cp.status = 'failed' THEN 1 ELSE 0 END) as failed_count
      FROM campaigns c
      LEFT JOIN campaign_platforms cp ON c.id = cp.campaign_id
      WHERE c.user_id = ?
      GROUP BY c.id
      ORDER BY c.created_at DESC
      LIMIT ? OFFSET ?
    `);

    return await stmt.bind(userId, limit, offset).all();
  }

  async update(campaignId, updateData) {
    const { title, description, budget, scheduleStart, scheduleEnd, status } = updateData;
    
    const stmt = this.db.prepare(`
      UPDATE campaigns 
      SET title = ?, description = ?, budget = ?, 
          schedule_start = ?, schedule_end = ?, status = ?,
          updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);

    await stmt.bind(
      title,
      description,
      budget,
      scheduleStart,
      scheduleEnd,
      status,
      campaignId
    ).run();

    return this.findById(campaignId);
  }

  async delete(campaignId) {
    // Campaign platforms and media will be deleted due to CASCADE constraints
    const stmt = this.db.prepare(`DELETE FROM campaigns WHERE id = ?`);
    await stmt.bind(campaignId).run();
  }

  async linkPlatforms(campaignId, platformIds) {
    for (const platformId of platformIds) {
      const cpId = uuidv4();
      const stmt = this.db.prepare(`
        INSERT INTO campaign_platforms (id, campaign_id, platform_id)
        VALUES (?, ?, ?)
      `);
      await stmt.bind(cpId, campaignId, platformId).run();
    }
  }

  async updatePlatformStatus(campaignId, platformId, status, errorMessage = null) {
    const stmt = this.db.prepare(`
      UPDATE campaign_platforms 
      SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
      WHERE campaign_id = ? AND platform_id = ?
    `);

    await stmt.bind(status, errorMessage, campaignId, platformId).run();
  }

  async getMedia(campaignId) {
    const stmt = this.db.prepare(`
      SELECT cm.*, m.filename, m.original_name, m.mime_type, m.size, m.url
      FROM campaign_media cm
      JOIN media m ON cm.media_id = m.id
      WHERE cm.campaign_id = ?
    `);

    return await stmt.bind(campaignId).all();
  }

  async duplicate(campaignId, newTitle) {
    const original = await this.findById(campaignId);
    if (!original) {
      throw new Error('Campaign not found');
    }

    const newCampaignData = {
      title: newTitle,
      description: original.description,
      budget: original.budget,
      scheduleStart: original.schedule_start,
      scheduleEnd: original.schedule_end,
      platforms: original.platforms?.map(p => p.platformId) || []
    };

    return await this.create(newCampaignData, original.user_id);
  }
}
