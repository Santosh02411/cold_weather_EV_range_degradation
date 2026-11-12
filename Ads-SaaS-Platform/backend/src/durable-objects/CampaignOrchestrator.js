import { adapterFactory } from '../adapters/AdapterFactory.js';
import { Log } from '../models/Log.js';

/**
 * Campaign Orchestrator Durable Object
 * Manages campaign state, handles retries, and coordinates platform operations
 */
export class CampaignOrchestrator {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.log = new Log(env.DB);
  }

  /**
   * Initialize the orchestrator for a campaign
   */
  async initialize(campaignId) {
    const existingState = await this.state.storage.get('campaignState');
    
    if (!existingState) {
      const initialState = {
        campaignId,
        status: 'initializing',
        platforms: {},
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      await this.state.storage.put('campaignState', initialState);
      await this.state.storage.put('platformStates', {});
      
      return initialState;
    }
    
    return existingState;
  }

  /**
   * Start campaign orchestration
   */
  async startCampaign(campaignId, platformIds) {
    const campaignState = await this.initialize(campaignId);
    
    campaignState.status = 'starting';
    campaignState.updatedAt = new Date().toISOString();
    
    // Initialize platform states
    const platformStates = {};
    for (const platformId of platformIds) {
      platformStates[platformId] = {
        status: 'pending',
        retryCount: 0,
        lastAttempt: null,
        nextRetry: null,
        error: null,
        externalId: null
      };
    }
    
    await this.state.storage.put('campaignState', campaignState);
    await this.state.storage.put('platformStates', platformStates);
    
    // Start processing platforms
    await this.processPlatforms(campaignId, platformIds);
    
    return campaignState;
  }

  /**
   * Process all platforms for a campaign
   */
  async processPlatforms(campaignId, platformIds) {
    const campaignState = await this.state.storage.get('campaignState');
    const platformStates = await this.state.storage.get('platformStates');
    
    campaignState.status = 'processing';
    campaignState.updatedAt = new Date().toISOString();
    
    await this.state.storage.put('campaignState', campaignState);
    
    // Process each platform
    for (const platformId of platformIds) {
      await this.processPlatform(campaignId, platformId);
    }
    
    // Check if all platforms are complete
    await this.checkCampaignCompletion(campaignId);
  }

  /**
   * Process a single platform
   */
  async processPlatform(campaignId, platformId) {
    const platformStates = await this.state.storage.get('platformStates');
    const platformState = platformStates[platformId];
    
    if (!platformState) {
      console.error(`Platform state not found for ${platformId}`);
      return;
    }
    
    // Check if we should retry
    if (platformState.status === 'failed' && platformState.nextRetry) {
      const now = new Date().toISOString();
      if (now < platformState.nextRetry) {
        // Not time to retry yet
        return;
      }
    }
    
    try {
      // Get platform configuration
      const platform = await this.getPlatform(platformId);
      if (!platform) {
        throw new Error(`Platform not found: ${platformId}`);
      }
      
      // Create adapter
      const adapter = adapterFactory.create(platform.type, platform);
      
      // Get campaign details
      const campaign = await this.getCampaign(campaignId);
      if (!campaign) {
        throw new Error(`Campaign not found: ${campaignId}`);
      }
      
      // Update platform state
      platformState.status = 'processing';
      platformState.lastAttempt = new Date().toISOString();
      platformState.error = null;
      
      await this.state.storage.put('platformStates', platformStates);
      
      // Prepare ad data
      const adData = await this.prepareAdData(campaign, platform);
      
      // Publish the ad
      const result = await adapter.publishAd(adData);
      
      // Update platform state on success
      platformState.status = 'success';
      platformState.externalId = result.externalId;
      platformState.retryCount = 0;
      platformState.nextRetry = null;
      
      // Update campaign platform status in database
      await this.updateCampaignPlatformStatus(campaignId, platformId, 'success');
      
      // Log success
      await this.log.info('Platform processing successful', {
        campaignId,
        platformId,
        externalId: result.externalId
      }, campaign.user_id, campaignId, platformId);
      
    } catch (error) {
      // Handle platform error
      platformState.status = 'failed';
      platformState.error = error.message;
      platformState.retryCount += 1;
      
      // Update campaign platform status in database
      await this.updateCampaignPlatformStatus(campaignId, platformId, 'failed', error.message);
      
      // Log error
      await this.log.error('Platform processing failed', {
        campaignId,
        platformId,
        error: error.message,
        retryCount: platformState.retryCount
      }, campaign.user_id, campaignId, platformId);
      
      // Schedule retry if appropriate
      if (this.shouldRetry(platformState, error)) {
        platformState.nextRetry = this.calculateNextRetry(platformState.retryCount);
      }
      
      // Send retry job to queue
      if (platformState.nextRetry) {
        await this.scheduleRetry(campaignId, platformId, platformState.nextRetry);
      }
    }
    
    await this.state.storage.put('platformStates', platformStates);
  }

  /**
   * Check if campaign processing is complete
   */
  async checkCampaignCompletion(campaignId) {
    const campaignState = await this.state.storage.get('campaignState');
    const platformStates = await this.state.storage.get('platformStates');
    
    const platformStatuses = Object.values(platformStates);
    const completedPlatforms = platformStatuses.filter(p => p.status === 'success');
    const failedPlatforms = platformStatuses.filter(p => p.status === 'failed');
    const pendingPlatforms = platformStatuses.filter(p => p.status === 'pending' || p.status === 'processing');
    
    if (pendingPlatforms.length === 0) {
      // All platforms processed
      if (failedPlatforms.length === 0) {
        campaignState.status = 'completed';
      } else {
        campaignState.status = 'partial_success';
      }
      
      campaignState.updatedAt = new Date().toISOString();
      await this.state.storage.put('campaignState', campaignState);
      
      // Log campaign completion
      await this.log.info('Campaign processing completed', {
        campaignId,
        status: campaignState.status,
        successCount: completedPlatforms.length,
        failedCount: failedPlatforms.length
      }, null, campaignId);
    }
  }

  /**
   * Retry a failed platform
   */
  async retryPlatform(campaignId, platformId) {
    const platformStates = await this.state.storage.get('platformStates');
    const platformState = platformStates[platformId];
    
    if (!platformState) {
      throw new Error(`Platform state not found: ${platformId}`);
    }
    
    // Reset platform state for retry
    platformState.status = 'pending';
    platformState.retryCount = 0;
    platformState.nextRetry = null;
    platformState.error = null;
    
    await this.state.storage.put('platformStates', platformStates);
    
    // Process the platform again
    await this.processPlatform(campaignId, platformId);
    
    return platformState;
  }

  /**
   * Get campaign state
   */
  async getCampaignState(campaignId) {
    const campaignState = await this.state.storage.get('campaignState');
    const platformStates = await this.state.storage.get('platformStates');
    
    return {
      campaign: campaignState,
      platforms: platformStates
    };
  }

  /**
   * Schedule a retry for a platform
   */
  async scheduleRetry(campaignId, platformId, retryTime) {
    const retryData = {
      campaignId,
      platformId,
      action: 'retry',
      scheduledAt: retryTime
    };
    
    // Send to queue with delay
    await this.env.CAMPAIGN_QUEUE.send(JSON.stringify(retryData), {
      delay: new Date(retryTime).getTime() - Date.now()
    });
  }

  /**
   * Prepare ad data for platform
   */
  async prepareAdData(campaign, platform) {
    // Get campaign media
    const mediaStmt = this.env.DB.prepare(`
      SELECT cm.*, m.filename, m.original_name, m.mime_type, m.size, m.url
      FROM campaign_media cm
      JOIN media m ON cm.media_id = m.id
      WHERE cm.campaign_id = ?
    `);
    
    const mediaItems = await mediaStmt.bind(campaign.id).all();
    
    // Prepare creative data
    const creative = mediaItems.length > 0 ? mediaItems[0] : this.getDefaultCreative();
    
    // Prepare targeting data
    const targeting = this.getDefaultTargeting();
    
    return {
      campaign: {
        title: campaign.title,
        objective: campaign.objective || 'TRAFFIC',
        ...campaign
      },
      creative,
      targeting,
      budget: campaign.budget
    };
  }

  /**
   * Get platform configuration from database
   */
  async getPlatform(platformId) {
    const stmt = this.env.DB.prepare(`
      SELECT id, name, type, config, user_id, is_connected
      FROM platforms WHERE id = ?
    `);

    const platform = await stmt.bind(platformId).first();
    
    if (platform && platform.config) {
      platform.config = JSON.parse(platform.config);
    }
    
    return platform;
  }

  /**
   * Get campaign details from database
   */
  async getCampaign(campaignId) {
    const stmt = this.env.DB.prepare(`
      SELECT id, title, description, budget, status, schedule_start, schedule_end, user_id
      FROM campaigns WHERE id = ?
    `);

    return await stmt.bind(campaignId).first();
  }

  /**
   * Update campaign platform status in database
   */
  async updateCampaignPlatformStatus(campaignId, platformId, status, error = null) {
    const stmt = this.env.DB.prepare(`
      UPDATE campaign_platforms 
      SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
      WHERE campaign_id = ? AND platform_id = ?
    `);

    await stmt.bind(status, error, campaignId, platformId).run();
  }

  /**
   * Determine if we should retry a failed platform
   */
  shouldRetry(platformState, error) {
    const maxRetries = 3;
    
    if (platformState.retryCount >= maxRetries) {
      return false;
    }
    
    // Check if error is retryable
    const retryableErrors = [
      'RATE_LIMITED',
      'TEMPORARY_FAILURE',
      'NETWORK_ERROR',
      'TIMEOUT',
      'SERVICE_UNAVAILABLE'
    ];
    
    return retryableErrors.some(code => error.message.includes(code)) ||
           error.message.includes('rate limit') ||
           error.message.includes('timeout') ||
           error.message.includes('network');
  }

  /**
   * Calculate next retry time with exponential backoff
   */
  calculateNextRetry(retryCount) {
    const baseDelay = 60000; // 1 minute
    const maxDelay = 3600000; // 1 hour
    const exponentialDelay = baseDelay * Math.pow(2, retryCount - 1);
    const delay = Math.min(exponentialDelay, maxDelay);
    
    return new Date(Date.now() + delay).toISOString();
  }

  /**
   * Get default creative data
   */
  getDefaultCreative() {
    return {
      type: 'image',
      headline: 'Default Headline',
      body: 'Default ad body text',
      url: 'https://example.com'
    };
  }

  /**
   * Get default targeting data
   */
  getDefaultTargeting() {
    return {
      ageMin: 18,
      ageMax: 65,
      genders: ['all'],
      locations: ['US'],
      interests: []
    };
  }

  /**
   * Handle incoming messages (for Durable Object communication)
   */
  async handleRequest(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;
    
    if (method === 'POST' && path === '/start') {
      const { campaignId, platformIds } = await request.json();
      return new Response(JSON.stringify(await this.startCampaign(campaignId, platformIds)));
    }
    
    if (method === 'POST' && path === '/retry') {
      const { campaignId, platformId } = await request.json();
      return new Response(JSON.stringify(await this.retryPlatform(campaignId, platformId)));
    }
    
    if (method === 'GET' && path === '/state') {
      const campaignId = url.searchParams.get('campaignId');
      return new Response(JSON.stringify(await this.getCampaignState(campaignId)));
    }
    
    return new Response('Not Found', { status: 404 });
  }

  /**
   * Fetch method for Durable Object
   */
  async fetch(request) {
    return this.handleRequest(request);
  }
}
