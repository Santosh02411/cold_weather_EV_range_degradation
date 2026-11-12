import { BaseAdapter } from '../BaseAdapter.js';

export class FacebookAdapter extends BaseAdapter {
  constructor(config) {
    super(config);
    this.apiVersion = 'v18.0';
    this.baseUrl = `https://graph.facebook.com/${this.apiVersion}`;
  }

  async connectPlatform(credentials) {
    try {
      const { accessToken, accountId } = credentials;
      
      // Validate credentials by making a test API call
      const response = await this.makeApiRequest(`/me?access_token=${accessToken}`);
      
      if (!response.id) {
        throw new Error('Invalid access token');
      }

      // Test account access
      const accountResponse = await this.makeApiRequest(
        `/act_${accountId}?access_token=${accessToken}&fields=name,account_status`
      );

      if (accountResponse.account_status !== 1) {
        throw new Error('Account is not active');
      }

      this.config.accessToken = accessToken;
      this.config.accountId = accountId;
      this.config.connectedAt = new Date().toISOString();

      this.log('info', 'Successfully connected to Facebook Ads', {
        accountId,
        accountName: accountResponse.name
      });

      return {
        success: true,
        platformId: this.config.id,
        externalAccountId: accountId,
        accountName: accountResponse.name
      };
    } catch (error) {
      this.log('error', 'Failed to connect to Facebook Ads', { error: error.message });
      throw this.handleError(error);
    }
  }

  async publishAd(adData) {
    try {
      const { campaign, creative, targeting, budget } = adData;
      
      // Step 1: Create campaign
      const campaignData = this.transformCampaignData({
        name: campaign.title,
        objective: this.getFacebookObjective(campaign.objective || 'OUTCOME_TRAFFIC'),
        special_ad_categories: [],
        status: 'PAUSED',
        buy_type: 'AUCTION'
      });

      const campaignResponse = await this.makeApiRequest(
        `/act_${this.config.accountId}/campaigns`,
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
        status: 'PAUSED'
      };

      const adSetResponse = await this.makeApiRequest(
        `/act_${this.config.accountId}/adsets`,
        'POST',
        adSetData
      );

      // Step 3: Create ad creative
      const creativeData = await this.transformCreative(creative);
      const creativeResponse = await this.makeApiRequest(
        `/act_${this.config.accountId}/adcreatives`,
        'POST',
        creativeData
      );

      // Step 4: Create ad
      const adData = {
        name: `${campaign.title} - Ad`,
        adset_id: adSetResponse.id,
        creative: { creative_id: creativeResponse.id },
        status: 'PAUSED'
      };

      const adResponse = await this.makeApiRequest(
        `/act_${this.config.accountId}/ads`,
        'POST',
        adData
      );

      this.log('info', 'Successfully published Facebook ad', {
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
      this.log('error', 'Failed to publish Facebook ad', { error: error.message });
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
        status: this.mapFacebookStatus(response.status),
        effectiveStatus: response.effective_status,
        lastUpdated: new Date().toISOString()
      };
    } catch (error) {
      this.log('error', 'Failed to get Facebook ad status', { 
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

      this.log('info', 'Successfully updated Facebook ad', { externalId });

      return {
        success: true,
        externalId,
        updatedFields: Object.keys(updateData)
      };
    } catch (error) {
      this.log('error', 'Failed to update Facebook ad', { 
        externalId, 
        error: error.message 
      });
      throw this.handleError(error);
    }
  }

  async deleteAd(externalId) {
    try {
      await this.makeApiRequest(`/${externalId}`, 'DELETE');

      this.log('info', 'Successfully deleted Facebook ad', { externalId });

      return {
        success: true,
        externalId
      };
    } catch (error) {
      this.log('error', 'Failed to delete Facebook ad', { 
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
        `/act_${this.config.accountId}/insights?${queryParams}`
      );

      return {
        success: true,
        data: response.data || [],
        pagination: response.paging
      };
    } catch (error) {
      this.log('error', 'Failed to get Facebook analytics', { error: error.message });
      throw this.handleError(error);
    }
  }

  async validateCredentials(credentials) {
    try {
      const { accessToken } = credentials;
      
      const response = await this.makeApiRequest(`/me?access_token=${accessToken}`);
      
      return !!response.id;
    } catch (error) {
      return false;
    }
  }

  getSupportedAdFormats() {
    return ['image', 'video', 'carousel', 'collection'];
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
    } else if (endpoint.includes('campaigns')) {
      return { id: 'camp_' + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes('adsets')) {
      return { id: 'adset_' + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes('ads')) {
      return { id: 'ad_' + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes('insights')) {
      return {
        data: [
          { impressions: 1000, clicks: 50, spend: 25.00 },
          { impressions: 1200, clicks: 60, spend: 30.00 }
        ]
      };
    } else {
      return { success: true };
    }
  }

  getFacebookObjective(objective) {
    const objectives = {
      'TRAFFIC': 'OUTCOME_TRAFFIC',
      'ENGAGEMENT': 'OUTCOME_ENGAGEMENT',
      'CONVERSIONS': 'OUTCOME_SALES',
      'LEADS': 'OUTCOME_LEADS',
      'AWARENESS': 'OUTCOME_AWARENESS'
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

  async transformCreative(creative) {
    const creativeData = {
      name: creative.name || 'Ad Creative',
      title: creative.headline || 'Default Headline',
      body: creative.body || 'Default body text',
      object_url: creative.url || 'https://example.com'
    };

    if (creative.image) {
      creativeData.image_hash = creative.image;
    }

    if (creative.video) {
      creativeData.video_id = creative.video;
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

  mapFacebookStatus(status) {
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
