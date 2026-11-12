import { v4 as uuidv4 } from 'uuid';

export class Media {
  constructor(db, r2Bucket) {
    this.db = db;
    this.r2Bucket = r2Bucket;
  }

  async create(mediaData, userId, file) {
    const { filename, originalName, mimeType, size } = mediaData;
    const mediaId = uuidv4();
    
    // Generate unique R2 key
    const r2Key = `${userId}/${mediaId}-${filename}`;
    
    // Upload file to R2
    const uploadedFile = await this.r2Bucket.put(r2Key, file);
    
    // Create database record
    const stmt = this.db.prepare(`
      INSERT INTO media (id, filename, original_name, mime_type, size, r2_key, url, user_id)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);

    await stmt.bind(
      mediaId,
      filename,
      originalName,
      mimeType,
      size,
      r2Key,
      uploadedFile.url,
      userId
    ).run();

    return this.findById(mediaId);
  }

  async findById(mediaId) {
    const stmt = this.db.prepare(`
      SELECT id, filename, original_name, mime_type, size, r2_key, url, user_id, created_at, updated_at
      FROM media WHERE id = ?
    `);

    return await stmt.bind(mediaId).first();
  }

  async findByUserId(userId, limit = 50, offset = 0) {
    const stmt = this.db.prepare(`
      SELECT id, filename, original_name, mime_type, size, url, created_at, updated_at
      FROM media WHERE user_id = ?
      ORDER BY created_at DESC
      LIMIT ? OFFSET ?
    `);

    return await stmt.bind(userId, limit, offset).all();
  }

  async delete(mediaId, userId) {
    // Get media info first
    const media = await this.findById(mediaId);
    if (!media) {
      throw new Error('Media not found');
    }

    // Check ownership
    if (media.user_id !== userId) {
      throw new Error('Unauthorized');
    }

    // Delete from R2
    await this.r2Bucket.delete(media.r2_key);

    // Delete from database
    const stmt = this.db.prepare(`DELETE FROM media WHERE id = ? AND user_id = ?`);
    await stmt.bind(mediaId, userId).run();
  }

  async linkToCampaign(mediaId, campaignId, mediaType, adCopy = null) {
    const linkId = uuidv4();
    
    const stmt = this.db.prepare(`
      INSERT INTO campaign_media (id, campaign_id, media_id, media_type, ad_copy)
      VALUES (?, ?, ?, ?, ?)
    `);

    await stmt.bind(linkId, campaignId, mediaId, mediaType, adCopy).run();
    
    return this.getCampaignMedia(campaignId);
  }

  async getCampaignMedia(campaignId) {
    const stmt = this.db.prepare(`
      SELECT cm.*, m.filename, m.original_name, m.mime_type, m.size, m.url
      FROM campaign_media cm
      JOIN media m ON cm.media_id = m.id
      WHERE cm.campaign_id = ?
      ORDER BY cm.created_at DESC
    `);

    return await stmt.bind(campaignId).all();
  }

  async unlinkFromCampaign(mediaId, campaignId) {
    const stmt = this.db.prepare(`
      DELETE FROM campaign_media 
      WHERE campaign_id = ? AND media_id = ?
    `);

    await stmt.bind(campaignId, mediaId).run();
    
    return this.getCampaignMedia(campaignId);
  }

  async getSignedUrl(mediaId, expiresIn = 3600) {
    const media = await this.findById(mediaId);
    if (!media) {
      throw new Error('Media not found');
    }

    // Generate signed URL for R2 access
    const signedUrl = await this.r2Bucket.createSignedUrl({
      key: media.r2_key,
      expiresIn: expiresIn
    });

    return signedUrl;
  }

  async updateMediaInfo(mediaId, userId, updateData) {
    const { filename, adCopy } = updateData;
    
    const stmt = this.db.prepare(`
      UPDATE media 
      SET filename = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ? AND user_id = ?
    `);

    await stmt.bind(filename, mediaId, userId).run();

    // Update ad copy if provided
    if (adCopy !== undefined) {
      const cmStmt = this.db.prepare(`
        UPDATE campaign_media 
        SET ad_copy = ?
        WHERE media_id = ?
      `);
      await cmStmt.bind(adCopy, mediaId).run();
    }

    return this.findById(mediaId);
  }

  async searchMedia(userId, query, limit = 20) {
    const stmt = this.db.prepare(`
      SELECT id, filename, original_name, mime_type, size, url, created_at, updated_at
      FROM media 
      WHERE user_id = ? AND (
        filename LIKE ? OR 
        original_name LIKE ?
      )
      ORDER BY created_at DESC
      LIMIT ?
    `);

    const searchPattern = `%${query}%`;
    return await stmt.bind(userId, searchPattern, searchPattern, limit).all();
  }

  async getMediaStats(userId) {
    const stmt = this.db.prepare(`
      SELECT 
        COUNT(*) as total_files,
        SUM(size) as total_size,
        COUNT(CASE WHEN mime_type LIKE 'image/%' THEN 1 END) as image_count,
        COUNT(CASE WHEN mime_type LIKE 'video/%' THEN 1 END) as video_count,
        COUNT(CASE WHEN mime_type LIKE 'text/%' THEN 1 END) as text_count
      FROM media 
      WHERE user_id = ?
    `);

    return await stmt.bind(userId).first();
  }
}
