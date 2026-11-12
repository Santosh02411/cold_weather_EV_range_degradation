import { Hono } from 'hono';
import { Campaign } from '../models/Campaign.js';
import { Log } from '../models/Log.js';

const campaigns = new Hono();

// Get all campaigns for user
campaigns.get('/', async (c) => {
  try {
    const userId = c.get('userId');
    const limit = parseInt(c.req.query('limit') || '50');
    const offset = parseInt(c.req.query('offset') || '0');

    const campaign = new Campaign(c.env.DB);
    const userCampaigns = await campaign.findByUserId(userId, limit, offset);

    return c.json({ campaigns: userCampaigns });
  } catch (error) {
    console.error('Get campaigns error:', error);
    return c.json({ error: 'Failed to get campaigns' }, 500);
  }
});

// Get single campaign
campaigns.get('/:id', async (c) => {
  try {
    const userId = c.get('userId');
    const campaignId = c.req.param('id');

    const campaign = new Campaign(c.env.DB);
    const foundCampaign = await campaign.findById(campaignId);

    if (!foundCampaign) {
      return c.json({ error: 'Campaign not found' }, 404);
    }

    if (foundCampaign.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    return c.json({ campaign: foundCampaign });
  } catch (error) {
    console.error('Get campaign error:', error);
    return c.json({ error: 'Failed to get campaign' }, 500);
  }
});

// Create new campaign
campaigns.post('/', async (c) => {
  try {
    const userId = c.get('userId');
    const campaignData = await c.req.json();

    // Validate required fields
    const { title, budget, platforms } = campaignData;
    if (!title || !budget || !platforms || platforms.length === 0) {
      return c.json({ error: 'Title, budget, and platforms are required' }, 400);
    }

    if (budget <= 0) {
      return c.json({ error: 'Budget must be greater than 0' }, 400);
    }

    const campaign = new Campaign(c.env.DB);
    const log = new Log(c.env.DB);

    const newCampaign = await campaign.create(campaignData, userId);

    await log.info('Campaign created', { 
      campaignId: newCampaign.id,
      title: newCampaign.title,
      platforms: platforms.length
    }, userId, newCampaign.id);

    return c.json({ campaign: newCampaign }, 201);
  } catch (error) {
    console.error('Create campaign error:', error);
    return c.json({ error: 'Failed to create campaign' }, 500);
  }
});

// Update campaign
campaigns.put('/:id', async (c) => {
  try {
    const userId = c.get('userId');
    const campaignId = c.req.param('id');
    const updateData = await c.req.json();

    const campaign = new Campaign(c.env.DB);
    const existingCampaign = await campaign.findById(campaignId);

    if (!existingCampaign) {
      return c.json({ error: 'Campaign not found' }, 404);
    }

    if (existingCampaign.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    const updatedCampaign = await campaign.update(campaignId, updateData);

    const log = new Log(c.env.DB);
    await log.info('Campaign updated', { 
      campaignId: campaignId,
      updates: Object.keys(updateData)
    }, userId, campaignId);

    return c.json({ campaign: updatedCampaign });
  } catch (error) {
    console.error('Update campaign error:', error);
    return c.json({ error: 'Failed to update campaign' }, 500);
  }
});

// Delete campaign
campaigns.delete('/:id', async (c) => {
  try {
    const userId = c.get('userId');
    const campaignId = c.req.param('id');

    const campaign = new Campaign(c.env.DB);
    const existingCampaign = await campaign.findById(campaignId);

    if (!existingCampaign) {
      return c.json({ error: 'Campaign not found' }, 404);
    }

    if (existingCampaign.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    await campaign.delete(campaignId);

    const log = new Log(c.env.DB);
    await log.info('Campaign deleted', { 
      campaignId: campaignId,
      title: existingCampaign.title
    }, userId);

    return c.json({ message: 'Campaign deleted successfully' });
  } catch (error) {
    console.error('Delete campaign error:', error);
    return c.json({ error: 'Failed to delete campaign' }, 500);
  }
});

// Publish campaign
campaigns.post('/:id/publish', async (c) => {
  try {
    const userId = c.get('userId');
    const campaignId = c.req.param('id');

    const campaign = new Campaign(c.env.DB);
    const foundCampaign = await campaign.findById(campaignId);

    if (!foundCampaign) {
      return c.json({ error: 'Campaign not found' }, 404);
    }

    if (foundCampaign.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    if (foundCampaign.status === 'active') {
      return c.json({ error: 'Campaign is already active' }, 400);
    }

    // Update campaign status
    await campaign.update(campaignId, { status: 'active' });

    // Create jobs for each platform
    const platforms = foundCampaign.platforms || [];
    const jobs = [];

    for (const platform of platforms) {
      const jobData = {
        campaignId,
        platformId: platform.platformId,
        action: 'publish',
        payload: {
          campaign: foundCampaign,
          platform
        }
      };

      // Send to queue
      await c.env.CAMPAIGN_QUEUE.send(JSON.stringify(jobData));
      
      jobs.push({
        platformId: platform.platformId,
        platformName: platform.platformName,
        status: 'queued'
      });
    }

    const log = new Log(c.env.DB);
    await log.info('Campaign published', { 
      campaignId: campaignId,
      platformsCount: platforms.length,
      jobs: jobs.length
    }, userId, campaignId);

    return c.json({ 
      message: 'Campaign published successfully',
      jobs
    });
  } catch (error) {
    console.error('Publish campaign error:', error);
    return c.json({ error: 'Failed to publish campaign' }, 500);
  }
});

// Duplicate campaign
campaigns.post('/:id/duplicate', async (c) => {
  try {
    const userId = c.get('userId');
    const campaignId = c.req.param('id');
    const { newTitle } = await c.req.json();

    if (!newTitle) {
      return c.json({ error: 'New title is required' }, 400);
    }

    const campaign = new Campaign(c.env.DB);
    const existingCampaign = await campaign.findById(campaignId);

    if (!existingCampaign) {
      return c.json({ error: 'Campaign not found' }, 404);
    }

    if (existingCampaign.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    const duplicatedCampaign = await campaign.duplicate(campaignId, newTitle);

    const log = new Log(c.env.DB);
    await log.info('Campaign duplicated', { 
      originalCampaignId: campaignId,
      newCampaignId: duplicatedCampaign.id,
      newTitle
    }, userId, duplicatedCampaign.id);

    return c.json({ campaign: duplicatedCampaign }, 201);
  } catch (error) {
    console.error('Duplicate campaign error:', error);
    return c.json({ error: 'Failed to duplicate campaign' }, 500);
  }
});

// Get campaign media
campaigns.get('/:id/media', async (c) => {
  try {
    const userId = c.get('userId');
    const campaignId = c.req.param('id');

    const campaign = new Campaign(c.env.DB);
    const existingCampaign = await campaign.findById(campaignId);

    if (!existingCampaign) {
      return c.json({ error: 'Campaign not found' }, 404);
    }

    if (existingCampaign.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    const media = await campaign.getMedia(campaignId);

    return c.json({ media });
  } catch (error) {
    console.error('Get campaign media error:', error);
    return c.json({ error: 'Failed to get campaign media' }, 500);
  }
});

export { campaigns as campaignRoutes };
