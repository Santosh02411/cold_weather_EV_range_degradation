import { adapterFactory } from '../adapters/AdapterFactory.js';
import { Log } from '../models/Log.js';

/**
 * Campaign Worker - Processes campaign jobs from the queue
 * Handles publishing, updating, and deleting ads across platforms
 */
export class CampaignWorker {
  constructor(env) {
    this.env = env;
    this.log = new Log(env.DB);
  }

  /**
   * Process a batch of messages from the queue
   * @param {Array} batch - Array of queue messages
   * @param {Object} env - Cloudflare environment
   */
  async processBatch(batch, env) {
    const results = [];

    for (const message of batch.messages) {
      try {
        const result = await this.processMessage(message, env);
        results.push(result);
        
        // Acknowledge message if processed successfully
        if (result.success) {
          message.ack();
        } else if (result.retry) {
          // Retry the message
          message.retry();
        } else {
          // Acknowledge failed message to prevent infinite retries
          message.ack();
        }
      } catch (error) {
        console.error('Error processing message:', error);
        message.retry();
        results.push({ success: false, error: error.message });
      }
    }

    return results;
  }

  /**
   * Process a single queue message
   * @param {Object} message - Queue message
   * @param {Object} env - Cloudflare environment
   */
  async processMessage(message, env) {
    const jobData = JSON.parse(message.body);
    const { campaignId, platformId, action, payload } = jobData;

    try {
      // Update job status to processing
      await this.updateJobStatus(jobData, 'processing');

      // Get platform configuration
      const platform = await this.getPlatform(platformId);
      if (!platform) {
        throw new Error(`Platform not found: ${platformId}`);
      }

      // Create adapter instance
      const adapter = adapterFactory.create(platform.type, platform);

      // Get campaign details
      const campaign = await this.getCampaign(campaignId);
      if (!campaign) {
        throw new Error(`Campaign not found: ${campaignId}`);
      }

      // Process the job based on action
      let result;
      switch (action) {
        case 'publish':
          result = await this.handlePublish(adapter, campaign, payload);
          break;
        case 'update':
          result = await this.handleUpdate(adapter, campaign, payload);
          break;
        case 'delete':
          result = await this.handleDelete(adapter, campaign, payload);
          break;
        default:
          throw new Error(`Unknown action: ${action}`);
      }

      // Update job status
      const jobStatus = result.success ? 'success' : 'failed';
      await this.updateJobStatus(jobData, jobStatus, result.error);

      // Update campaign platform status
      await this.updateCampaignPlatformStatus(campaignId, platformId, jobStatus, result.error);

      // Log the result
      await this.log.info(`Campaign ${action} ${jobStatus}`, {
        campaignId,
        platformId,
        action,
        result
      }, campaign.user_id, campaignId, platformId);

      return {
        success: result.success,
        campaignId,
        platformId,
        action,
        result
      };

    } catch (error) {
      // Log the error
      await this.log.error(`Campaign ${action} failed`, {
        campaignId,
        platformId,
        action,
        error: error.message
      }, null, campaignId, platformId);

      // Update job status to failed
      await this.updateJobStatus(jobData, 'failed', error.message);

      return {
        success: false,
        campaignId,
        platformId,
        action,
        error: error.message,
        retry: this.shouldRetry(error)
      };
    }
  }

  /**
   * Handle publish action
   */
  async handlePublish(adapter, campaign, payload) {
    try {
      const { platform, creative, targeting, budget } = payload;
      
      // Prepare ad data
      const adData = {
        campaign: {
          title: campaign.title,
          objective: campaign.objective,
          ...campaign
        },
        creative: creative || this.getDefaultCreative(),
        targeting: targeting || this.getDefaultTargeting(),
        budget: budget || campaign.budget
      };

      // Publish the ad
      const result = await adapter.publishAd(adData);
      
      return {
        success: true,
        externalId: result.externalId,
        platformData: result
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Handle update action
   */
  async handleUpdate(adapter, campaign, payload) {
    try {
      const { externalId, updateData } = payload;
      
      const result = await adapter.updateAd(externalId, updateData);
      
      return {
        success: true,
        externalId,
        platformData: result
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Handle delete action
   */
  async handleDelete(adapter, campaign, payload) {
    try {
      const { externalId } = payload;
      
      const result = await adapter.deleteAd(externalId);
      
      return {
        success: true,
        externalId,
        platformData: result
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
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
   * Update job status in database
   */
  async updateJobStatus(jobData, status, error = null) {
    const { campaignId, platformId, action } = jobData;

    // Create or update job record
    const stmt = this.env.DB.prepare(`
      INSERT OR REPLACE INTO jobs 
      (id, campaign_id, platform_id, action, status, payload, error_message, processed_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const jobId = this.generateJobId(campaignId, platformId, action);
    
    await stmt.bind(
      jobId,
      campaignId,
      platformId,
      action,
      status,
      JSON.stringify(jobData),
      error,
      status === 'success' || status === 'failed' ? new Date().toISOString() : null,
      new Date().toISOString()
    ).run();
  }

  /**
   * Update campaign platform status
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
   * Generate unique job ID
   */
  generateJobId(campaignId, platformId, action) {
    return `job_${campaignId}_${platformId}_${action}_${Date.now()}`;
  }

  /**
   * Determine if an error should trigger a retry
   */
  shouldRetry(error) {
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
   * Handle rate limiting
   */
  async handleRateLimit(adapter, error) {
    const rateLimitInfo = adapter.getRateLimitInfo();
    const delay = this.calculateRetryDelay(error, rateLimitInfo);
    
    console.log(`Rate limited. Retrying in ${delay}ms`);
    await new Promise(resolve => setTimeout(resolve, delay));
  }

  /**
   * Calculate retry delay based on error and rate limit info
   */
  calculateRetryDelay(error, rateLimitInfo) {
    // Base delay with exponential backoff
    const baseDelay = 1000;
    const maxDelay = 30000; // 30 seconds max
    const jitter = Math.random() * 1000; // Add randomness
    
    // If we have rate limit info, use it
    if (rateLimitInfo.resetTime) {
      const resetDelay = new Date(rateLimitInfo.resetTime).getTime() - Date.now();
      return Math.min(Math.max(resetDelay, baseDelay), maxDelay) + jitter;
    }
    
    // Exponential backoff
    return Math.min(baseDelay * Math.pow(2, error.retryCount || 1), maxDelay) + jitter;
  }
}

// Export the worker handler
export default {
  async queue(batch, env) {
    const worker = new CampaignWorker(env);
    return await worker.processBatch(batch, env);
  }
};
