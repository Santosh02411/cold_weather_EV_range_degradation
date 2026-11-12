import { Hono } from 'hono';
import { Media } from '../models/Media.js';
import { Log } from '../models/Log.js';

const media = new Hono();

// Get all media for user
media.get('/', async (c) => {
  try {
    const userId = c.get('userId');
    const limit = parseInt(c.req.query('limit') || '50');
    const offset = parseInt(c.req.query('offset') || '0');
    const search = c.req.query('search');

    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    
    let mediaFiles;
    if (search) {
      mediaFiles = await mediaModel.searchMedia(userId, search, limit);
    } else {
      mediaFiles = await mediaModel.findByUserId(userId, limit, offset);
    }

    return c.json({ media: mediaFiles });
  } catch (error) {
    console.error('Get media error:', error);
    return c.json({ error: 'Failed to get media' }, 500);
  }
});

// Get single media file
media.get('/:id', async (c) => {
  try {
    const userId = c.get('userId');
    const mediaId = c.req.param('id');

    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const mediaFile = await mediaModel.findById(mediaId);

    if (!mediaFile) {
      return c.json({ error: 'Media not found' }, 404);
    }

    if (mediaFile.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    return c.json({ media: mediaFile });
  } catch (error) {
    console.error('Get media error:', error);
    return c.json({ error: 'Failed to get media' }, 500);
  }
});

// Upload media file
media.post('/', async (c) => {
  try {
    const userId = c.get('userId');
    
    // Get form data
    const formData = await c.req.formData();
    const file = formData.get('file');
    
    if (!file) {
      return c.json({ error: 'No file provided' }, 400);
    }

    // Validate file
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'video/quicktime', 'text/plain'];
    if (!validTypes.includes(file.type)) {
      return c.json({ error: 'Invalid file type. Supported types: JPEG, PNG, GIF, MP4, MOV, TXT' }, 400);
    }

    // Check file size (50MB limit)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      return c.json({ error: 'File too large. Maximum size is 50MB' }, 400);
    }

    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const log = new Log(c.env.DB);

    const mediaData = {
      filename: file.name,
      originalName: file.name,
      mimeType: file.type,
      size: file.size
    };

    const newMedia = await mediaModel.create(mediaData, userId, file);

    await log.info('Media uploaded', { 
      mediaId: newMedia.id,
      filename: newMedia.filename,
      size: newMedia.size,
      mimeType: newMedia.mime_type
    }, userId);

    return c.json({ media: newMedia }, 201);
  } catch (error) {
    console.error('Upload media error:', error);
    return c.json({ error: 'Failed to upload media' }, 500);
  }
});

// Delete media file
media.delete('/:id', async (c) => {
  try {
    const userId = c.get('userId');
    const mediaId = c.req.param('id');

    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const log = new Log(c.env.DB);

    // Check if media exists and user owns it
    const mediaFile = await mediaModel.findById(mediaId);
    if (!mediaFile) {
      return c.json({ error: 'Media not found' }, 404);
    }

    if (mediaFile.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    await mediaModel.delete(mediaId, userId);

    await log.info('Media deleted', { 
      mediaId: mediaId,
      filename: mediaFile.filename
    }, userId);

    return c.json({ message: 'Media deleted successfully' });
  } catch (error) {
    console.error('Delete media error:', error);
    return c.json({ error: 'Failed to delete media' }, 500);
  }
});

// Link media to campaign
media.post('/:id/link-to-campaign', async (c) => {
  try {
    const userId = c.get('userId');
    const mediaId = c.req.param('id');
    const { campaignId, mediaType, adCopy } = await c.req.json();

    if (!campaignId || !mediaType) {
      return c.json({ error: 'Campaign ID and media type are required' }, 400);
    }

    const validTypes = ['image', 'video', 'text'];
    if (!validTypes.includes(mediaType)) {
      return c.json({ error: 'Invalid media type' }, 400);
    }

    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const log = new Log(c.env.DB);

    // Check if media exists and user owns it
    const mediaFile = await mediaModel.findById(mediaId);
    if (!mediaFile) {
      return c.json({ error: 'Media not found' }, 404);
    }

    if (mediaFile.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    // Check if campaign exists and user owns it
    const campaignCheck = await c.env.DB.prepare(`
      SELECT id FROM campaigns WHERE id = ? AND user_id = ?
    `).bind(campaignId, userId).first();

    if (!campaignCheck) {
      return c.json({ error: 'Campaign not found or unauthorized' }, 404);
    }

    const campaignMedia = await mediaModel.linkToCampaign(mediaId, campaignId, mediaType, adCopy);

    await log.info('Media linked to campaign', { 
      mediaId: mediaId,
      campaignId: campaignId,
      mediaType: mediaType
    }, userId, campaignId);

    return c.json({ campaignMedia }, 201);
  } catch (error) {
    console.error('Link media to campaign error:', error);
    return c.json({ error: 'Failed to link media to campaign' }, 500);
  }
});

// Unlink media from campaign
media.delete('/:id/unlink-from-campaign', async (c) => {
  try {
    const userId = c.get('userId');
    const mediaId = c.req.param('id');
    const campaignId = c.req.query('campaignId');

    if (!campaignId) {
      return c.json({ error: 'Campaign ID is required' }, 400);
    }

    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const log = new Log(c.env.DB);

    // Check if media exists and user owns it
    const mediaFile = await mediaModel.findById(mediaId);
    if (!mediaFile) {
      return c.json({ error: 'Media not found' }, 404);
    }

    if (mediaFile.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    // Check if campaign exists and user owns it
    const campaignCheck = await c.env.DB.prepare(`
      SELECT id FROM campaigns WHERE id = ? AND user_id = ?
    `).bind(campaignId, userId).first();

    if (!campaignCheck) {
      return c.json({ error: 'Campaign not found or unauthorized' }, 404);
    }

    await mediaModel.unlinkFromCampaign(mediaId, campaignId);

    await log.info('Media unlinked from campaign', { 
      mediaId: mediaId,
      campaignId: campaignId
    }, userId, campaignId);

    return c.json({ message: 'Media unlinked from campaign successfully' });
  } catch (error) {
    console.error('Unlink media from campaign error:', error);
    return c.json({ error: 'Failed to unlink media from campaign' }, 500);
  }
});

// Get signed URL for media
media.get('/:id/signed-url', async (c) => {
  try {
    const userId = c.get('userId');
    const mediaId = c.req.param('id');
    const expiresIn = parseInt(c.req.query('expiresIn') || '3600');

    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);

    // Check if media exists and user owns it
    const mediaFile = await mediaModel.findById(mediaId);
    if (!mediaFile) {
      return c.json({ error: 'Media not found' }, 404);
    }

    if (mediaFile.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    const signedUrl = await mediaModel.getSignedUrl(mediaId, expiresIn);

    return c.json({ signedUrl });
  } catch (error) {
    console.error('Get signed URL error:', error);
    return c.json({ error: 'Failed to get signed URL' }, 500);
  }
});

// Get media stats
media.get('/stats/summary', async (c) => {
  try {
    const userId = c.get('userId');

    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const stats = await mediaModel.getMediaStats(userId);

    return c.json({ stats });
  } catch (error) {
    console.error('Get media stats error:', error);
    return c.json({ error: 'Failed to get media stats' }, 500);
  }
});

export { media as mediaRoutes };
