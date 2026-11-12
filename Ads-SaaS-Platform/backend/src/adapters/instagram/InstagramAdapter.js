import { BaseAdapter } from '../BaseAdapter.js';

export class InstagramAdapter extends BaseAdapter {
  constructor(config) {
    super(config);
    this.apiVersion = 'v18.0';
    this.baseUrl = `https://graph.facebook.com/${this.apiVersion}`;
  }

  async connectPlatform(credentials) {
    try {
      const { accessToken, businessAccountId } = credentials;
      
      // Validate credentials by making a test API call
      const response = await this.makeApiRequest(`/me?access_token=${accessToken}`);
      
      if (!response.id) {
        throw new Error('Invalid access token');
      }

      // Test Instagram business account access
      const igResponse = await this.makeApiRequest(
        `/${businessAccountId}?fields=instagram_business_account&access_token=${accessToken}`
      );

      if (!igResponse.instagram_business_account) {
        throw new Error('Invalid Instagram business account');
      }

      // Get Instagram account details
      const igDetails = await this.makeApiRequest(
        `/${igResponse.instagram_business_account.id}?fields=username,followers_count,media_count&access_token=${accessToken}`
      );

      this.config.accessToken = accessToken;
      this.config.businessAccountId = businessAccountId;
      this.config.instagramAccountId = igResponse.instagram_business_account.id;
      this.config.connectedAt = new Date().toISOString();

      this.log('info', 'Successfully connected to Instagram Business', {
        businessAccountId,
        instagramAccountId: igResponse.instagram_business_account.id,
        username: igDetails.username
      });

      return {
        success: true,
        platformId: this.config.id,
        externalAccountId: igResponse.instagram_business_account.id,
        accountName: `@${igDetails.username}`,
        followers: igDetails.followers_count
      };
    } catch (error) {
      this.log('error', 'Failed to connect to Instagram Business', { error: error.message });
      throw this.handleError(error);
    }
  }

  async publishAd(adData) {
    try {
      const { campaign, creative, targeting, budget } = adData;
      
      // Step 1: Create campaign
      const campaignData = this.transformCampaignData({
        name: campaign.title,
        objective: this.getInstagramObjective(campaign.objective || 'OUTCOME_TRAFFIC'),
        special_ad_categories: [],
        status: 'PAUSED',
        buy_type: 'AUCTION'
      });

      const campaignResponse = await this.makeApiRequest(
        `/act_${this.config.businessAccountId}/campaigns`,
        'POST',
        campaignData
      );

      // Step 2: Create ad set
      const adSetData = {
        name: `${campaign.title} - Ad Set`,
        campaign_id: campaignResponse.id,
        optimization_goal: 'IMPRESSIONS',
        billing_event: 'IMPRESSIONS',
        bid_amount: 100,
        daily_budget: budget * 100, // Convert to cents
        targeting: this.transformTargeting(targeting),
        promoted_object: {
          object_type: 'PAGE',
          page_id: this.config.businessAccountId
        },
        status: 'PAUSED'
      };

      const adSetResponse = await this.makeApiRequest(
        `/act_${this.config.businessAccountId}/adsets`,
        'POST',
        adSetData
      );

      // Step 3: Create Instagram ad creative
      const creativeData = await this.transformInstagramCreative(creative);
      const creativeResponse = await this.makeApiRequest(
        `/act_${this.config.businessAccountId}/adcreatives`,
        'POST',
        creativeData
      );

      // Step 4: Create ad
      const adData = {
        name: `${campaign.title} - Instagram Ad`,
        adset_id: adSetResponse.id,
        creative: { creative_id: creativeResponse.id },
        status: 'PAUSED'
      };

      const adResponse = await this.makeApiRequest(
        `/act_${this.config.businessAccountId}/ads`,
        'POST',
        adData
      );

      this.log('info', 'Successfully published Instagram ad', {
        campaignId: campaignResponse.id,
        adSetId: adSetResponse.id,
        adId: adResponse.id
      });

      return {
        success: true,
        externalId: adResponse.id,
        campaignId: campaignResponse.id,
        adSetId: adSetResponse.id,
        creativeId: creativeResponse.id,
        status: 'published'
      };
    } catch (error) {
      this.log('error', 'Failed to publish Instagram ad', { error: error.message });
      throw this.handleError(error);
    }
  }

  async getStatus(externalId) {
    try {
      const response = await this.makeApiRequest(
        `/${externalId}?fields=status,effective_status`
      );

      return {
        success: true,
        status: this.mapInstagramStatus(response.status),
        effectiveStatus: response.effective_status,
        lastUpdated: new Date().toISOString()
      };
    } catch (error) {
      this.log('error', 'Failed to get Instagram ad status', { 
        externalId, 
        error: error.message 
      });
      throw this.handleError(error);
    }
  }

  async updateAd(externalId, updateData) {
    try {
      const updates = this.transformUpdateData(updateData);
      
      const response = await this.makeApiRequest(
        `/${externalId}`,
        'POST',
        updates
      );

      this.log('info', 'Successfully updated Instagram ad', { externalId });

      return {
        success: true,
        externalId,
        updatedFields: Object.keys(updateData)
      };
    } catch (error) {
      this.log('error', 'Failed to update Instagram ad', { 
        externalId, 
        error: error.message 
      });
      throw this.handleError(error);
    }
  }

  async deleteAd(externalId) {
    try {
      await this.makeApiRequest(`/${externalId}`, 'DELETE');

      this.log('info', 'Successfully deleted Instagram ad', { externalId });

      return {
        success: true,
        externalId
      };
    } catch (error) {
      this.log('error', 'Failed to delete Instagram ad', { 
        externalId, 
        error: error.message 
      });
      throw this.handleError(error);
    }
  }

  async getAnalytics(filters = {}) {
    try {
      const { datePreset = 'last_7d', metrics = ['impressions', 'clicks', 'spend'] } = filters;
      
      const queryParams = new URLSearchParams({
        fields: metrics.join(','),
        date_preset: datePreset
      });

      const response = await this.makeApiRequest(
        `/act_${this.config.businessAccountId}/insights?${queryParams}`
      );

      return {
        success: true,
        data: response.data || [],
        pagination: response.paging
      };
    } catch (error) {
      this.log('error', 'Failed to get Instagram analytics', { error: error.message });
      throw this.handleError(error);
    }
  }

  async validateCredentials(credentials) {
    try {
      const { accessToken, businessAccountId } = credentials;
      
      const response = await this.makeApiRequest(
        `/${businessAccountId}?fields=instagram_business_account&access_token=${accessToken}`
      );
      
      return !!response.instagram_business_account;
    } catch (error) {
      return false;
    }
  }

  getSupportedAdFormats() {
    return ['image', 'video', 'carousel', 'stories', 'reels'];
  }

  getTargetingOptions() {
    return [
      'age',
      'gender',
      'location',
      'interests',
      'behaviors',
      'custom_audiences',
      'lookalike_audiences',
      'education',
      'work',
      'relationship',
      'language'
    ];
  }

  // Helper methods
  async makeApiRequest(endpoint, method = 'GET', data = null) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json'
    };

    let options = { headers, method };

    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }

    // Simulate API call for demo
    await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));

    // Mock response - in production, this would be a real fetch call
    if (endpoint.includes('/me')) {
      return { id: '123456789', name: 'Test User' };
    } else if (endpoint.includes('instagram_business_account')) {
      return {
        instagram_business_account: {
          id: 'ig_' + Math.random().toString(36).substr(2, 9)
        }
      };
    } else if (endpoint.includes('username,followers_count,media_count')) {
      return {
        username: 'test_business',
        followers_count: 10000,
        media_count: 150
      };
    } else if (endpoint.includes('campaigns')) {
      return { id: 'camp_' + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes('adsets')) {
      return { id: 'adset_' + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes('ads')) {
      return { id: 'ad_' + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes('insights')) {
      return {
        data: [
          { impressions: 800, clicks: 40, spend: 20.00 },
          { impressions: 950, clicks: 55, spend: 28.00 }
        ]
      };
    } else {
      return { success: true };
    }
  }

  getInstagramObjective(objective) {
    const objectives = {
      'TRAFFIC': 'OUTCOME_TRAFFIC',
      'ENGAGEMENT': 'OUTCOME_ENGAGEMENT',
      'CONVERSIONS': 'OUTCOME_SALES',
      'LEADS': 'OUTCOME_LEADS',
      'AWARENESS': 'OUTCOME_AWARENESS',
      'REACH': 'OUTCOME_REACH'
    };
    return objectives[objective] || 'OUTCOME_TRAFFIC';
  }

  transformCampaignData(campaignData) {
    return {
      ...campaignData,
      access_token: this.config.accessToken
    };
  }

  transformTargeting(targeting) {
    return {
      age_min: targeting.ageMin || 18,
      age_max: targeting.ageMax || 65,
      genders: targeting.genders || [1, 2],
      geo_locations: targeting.locations || [],
      interests: targeting.interests || [],
      behaviors: targeting.behaviors || []
    };
  }

  async transformInstagramCreative(creative) {
    const creativeData = {
      name: creative.name || 'Instagram Ad Creative',
      object_story_spec: {
        page_id: this.config.businessAccountId,
        instagram_actor_id: this.config.instagramAccountId
      }
    };

    if (creative.type === 'image') {
      creativeData.object_story_spec.link_data = {
        image_hash: creative.image,
        link: creative.url || 'https://example.com',
        message: creative.caption || 'Default caption',
        call_to_action: {
          type: creative.cta || 'LEARN_MORE',
          value: { link: creative.url || 'https://example.com' }
        }
      };
    } else if (creative.type === 'video') {
      creativeData.object_story_spec.link_data = {
        video_id: creative.video,
        link: creative.url || 'https://example.com',
        message: creative.caption || 'Default caption',
        call_to_action: {
          type: creative.cta || 'LEARN_MORE',
          value: { link: creative.url || 'https://example.com' }
        }
      };
    } else if (creative.type === 'carousel') {
      creativeData.object_story_spec.link_data = {
        child_attachments: creative.carouselItems || [],
        link: creative.url || 'https://example.com',
        message: creative.caption || 'Default caption'
      };
    }

    return creativeData;
  }

  transformUpdateData(updateData) {
    const transformed = {};
    
    if (updateData.status) {
      transformed.status = updateData.status.toUpperCase();
    }
    
    if (updateData.name) {
      transformed.name = updateData.name;
    }

    return transformed;
  }

  mapInstagramStatus(status) {
    const statusMap = {
      'ACTIVE': 'active',
      'PAUSED': 'paused',
      'ARCHIVED': 'archived',
      'DELETED': 'deleted'
    };
    return statusMap[status] || 'unknown';
  }

  isRetryableError(error) {
    const retryablePatterns = [
      /rate limit/i,
      /timeout/i,
      /network/i,
      /temporary/i,
      /service unavailable/i
    ];

    return retryablePatterns.some(pattern => pattern.test(error.message)) ||
           error.code === 'API_EC_SERVICE' ||
           error.code === 'API_EC_TOO_MANY_CALLS';
  }
}
