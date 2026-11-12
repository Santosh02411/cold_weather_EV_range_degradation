import { BaseAdapter } from '../BaseAdapter.js';

export class TikTokAdapter extends BaseAdapter {
  constructor(config) {
    super(config);
    this.apiVersion = 'v1.3';
    this.baseUrl = 'https://business-api.tiktok.com/open_api/v1.3';
  }

  async connectPlatform(credentials) {
    try {
      const { accessToken, appId } = credentials;
      
      // Validate credentials by making a test API call
      const response = await this.makeApiRequest(
        '/user/info/',
        'GET',
        null,
        accessToken
      );
      
      if (!response.data?.user_info) {
        throw new Error('Invalid access token');
      }

      // Test app access
      const appResponse = await this.makeApiRequest(
        '/advertiser/get/',
        'GET',
        { app_id: appId },
        accessToken
      );

      this.config.accessToken = accessToken;
      this.config.appId = appId;
      this.config.connectedAt = new Date().toISOString();

      this.log('info', 'Successfully connected to TikTok Ads', {
        appId,
        advertiserId: appResponse.data?.advertiser_id
      });

      return {
        success: true,
        platformId: this.config.id,
        externalAccountId: appResponse.data?.advertiser_id,
        accountName: appResponse.data?.name || 'TikTok Ads Account'
      };
    } catch (error) {
      this.log('error', 'Failed to connect to TikTok Ads', { error: error.message });
      throw this.handleError(error);
    }
  }

  async publishAd(adData) {
    try {
      const { campaign, creative, targeting, budget } = adData;
      
      // Step 1: Create campaign
      const campaignData = this.transformCampaignData({
        advertiser_id: this.config.advertiserId,
        campaign_name: campaign.title,
        objective: this.getTikTokObjective(campaign.objective || 'TRAFFIC'),
        budget_optimization_mode: 'BUDGET_OPTIMIZATION_MODE_INFINITE',
        budget: budget * 100, // Convert to cents
        status: 'DELIVER'
      });

      const campaignResponse = await this.makeApiRequest(
        '/campaign/create/',
        'POST',
        campaignData
      );

      // Step 2: Create ad group
      const adGroupData = {
        advertiser_id: this.config.advertiserId,
        campaign_id: campaignResponse.data.campaign_id,
        adgroup_name: `${campaign.title} - Ad Group`,
        budget: budget * 100,
        targeting_spec: this.transformTargeting(targeting),
        status: 'DELIVER'
      };

      const adGroupResponse = await this.makeApiRequest(
        '/adgroup/create/',
        'POST',
        adGroupData
      );

      // Step 3: Create ad creative
      const creativeData = await this.transformCreative(creative);
      const creativeResponse = await this.makeApiRequest(
        '/ad/create/',
        'POST',
        {
          advertiser_id: this.config.advertiserId,
          adgroup_id: adGroupResponse.data.adgroup_id,
          ...creativeData
        }
      );

      this.log('info', 'Successfully published TikTok ad', {
        campaignId: campaignResponse.data.campaign_id,
        adGroupId: adGroupResponse.data.adgroup_id,
        adId: creativeResponse.data.ad_id
      });

      return {
        success: true,
        externalId: creativeResponse.data.ad_id,
        campaignId: campaignResponse.data.campaign_id,
        adGroupId: adGroupResponse.data.adgroup_id,
        status: 'published'
      };
    } catch (error) {
      this.log('error', 'Failed to publish TikTok ad', { error: error.message });
      throw this.handleError(error);
    }
  }

  async getStatus(externalId) {
    try {
      const response = await this.makeApiRequest(
        '/ad/get/',
        'GET',
        {
          advertiser_id: this.config.advertiserId,
          ad_ids: [externalId]
        }
      );

      const ad = response.data?.list?.[0];
      
      return {
        success: true,
        status: this.mapTikTokStatus(ad?.status),
        adName: ad?.ad_name,
        lastUpdated: new Date().toISOString()
      };
    } catch (error) {
      this.log('error', 'Failed to get TikTok ad status', { 
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
        '/ad/update/',
        'POST',
        {
          advertiser_id: this.config.advertiserId,
          ad_id: externalId,
          ...updates
        }
      );

      this.log('info', 'Successfully updated TikTok ad', { externalId });

      return {
        success: true,
        externalId,
        updatedFields: Object.keys(updateData)
      };
    } catch (error) {
      this.log('error', 'Failed to update TikTok ad', { 
        externalId, 
        error: error.message 
      });
      throw this.handleError(error);
    }
  }

  async deleteAd(externalId) {
    try {
      await this.makeApiRequest(
        '/ad/delete/',
        'POST',
        {
          advertiser_id: this.config.advertiserId,
          ad_ids: [externalId]
        }
      );

      this.log('info', 'Successfully deleted TikTok ad', { externalId });

      return {
        success: true,
        externalId
      };
    } catch (error) {
      this.log('error', 'Failed to delete TikTok ad', { 
        externalId, 
        error: error.message 
      });
      throw this.handleError(error);
    }
  }

  async getAnalytics(filters = {}) {
    try {
      const { 
        startDate = '2024-01-01', 
        endDate = '2024-01-07',
        metrics = ['impressions', 'clicks', 'spend'] 
      } = filters;
      
      const response = await this.makeApiRequest(
        '/ad/get/',
        'GET',
        {
          advertiser_id: this.config.advertiserId,
          start_date: startDate,
          end_date: endDate,
          fields: metrics.join(','),
          page_size: 100
        }
      );

      return {
        success: true,
        data: response.data?.list || [],
        pagination: response.page_info
      };
    } catch (error) {
      this.log('error', 'Failed to get TikTok analytics', { error: error.message });
      throw this.handleError(error);
    }
  }

  async validateCredentials(credentials) {
    try {
      const { accessToken } = credentials;
      
      const response = await this.makeApiRequest(
        '/user/info/',
        'GET',
        null,
        accessToken
      );
      
      return !!response.data?.user_info;
    } catch (error) {
      return false;
    }
  }

  getSupportedAdFormats() {
    return ['video', 'image', 'spark_ad', 'collection_ad'];
  }

  getTargetingOptions() {
    return [
      'age',
      'gender',
      'location',
      'interests',
      'behaviors',
      'device_type',
      'carrier',
      'language'
    ];
  }

  // Helper methods
  async makeApiRequest(endpoint, method = 'GET', data = null, accessToken = null) {
    const token = accessToken || this.config.accessToken;
    let url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Access-Token': token,
      'Content-Type': 'application/json'
    };

    let options = { headers, method };

    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    } else if (data && method === 'GET') {
      // For GET requests, add data as query parameters
      const params = new URLSearchParams(data);
      url += `?${params}`;
    }

    // Simulate API call for demo
    await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));

    // Mock response - in production, this would be a real fetch call
    if (endpoint.includes('/user/info/')) {
      return {
        data: {
          user_info: { id: '123456789', name: 'Test User' }
        }
      };
    } else if (endpoint.includes('/advertiser/get/')) {
      return {
        data: {
          advertiser_id: 'adv_' + Math.random().toString(36).substr(2, 9),
          name: 'Test Advertiser'
        }
      };
    } else if (endpoint.includes('/campaign/create/')) {
      return {
        data: {
          campaign_id: 'camp_' + Math.random().toString(36).substr(2, 9)
        }
      };
    } else if (endpoint.includes('/adgroup/create/')) {
      return {
        data: {
          adgroup_id: 'adg_' + Math.random().toString(36).substr(2, 9)
        }
      };
    } else if (endpoint.includes('/ad/create/')) {
      return {
        data: {
          ad_id: 'ad_' + Math.random().toString(36).substr(2, 9)
        }
      };
    } else if (endpoint.includes('/ad/get/')) {
      return {
        data: {
          list: [
            { 
              ad_id: 'ad_123', 
              ad_name: 'Test Ad', 
              status: 'STATUS_DELIVER' 
            }
          ]
        }
      };
    } else {
      return { success: true };
    }
  }

  getTikTokObjective(objective) {
    const objectives = {
      'TRAFFIC': 'TRAFFIC',
      'CONVERSIONS': 'CONVERSIONS',
      'APP_INSTALL': 'APP_INSTALL',
      'VIDEO_VIEWS': 'VIDEO_VIEWS',
      'LEAD_GENERATION': 'LEAD_GENERATION',
      'MESSAGES': 'MESSAGES'
    };
    return objectives[objective] || 'TRAFFIC';
  }

  transformCampaignData(campaignData) {
    return {
      ...campaignData,
      budget_optimization_mode: 'BUDGET_OPTIMIZATION_MODE_INFINITE',
      status: 'DELIVER'
    };
  }

  transformTargeting(targeting) {
    return {
      targeting_spec: {
        age_groups: targeting.ageGroups || ['AGE_18_24', 'AGE_25_34'],
        gender: targeting.gender || ['GENDER_MALE', 'GENDER_FEMALE'],
        geo_locations: targeting.locations || [],
        interests: targeting.interests || [],
        behaviors: targeting.behaviors || []
      }
    };
  }

  async transformCreative(creative) {
    const creativeData = {
      ad_name: creative.name || 'TikTok Ad',
      ad_format: creative.format || 'VIDEO_AD'
    };

    if (creative.video) {
      creativeData.video_id = creative.video;
    }

    if (creative.image) {
      creativeData.image_id = creative.image;
    }

    if (creative.headline) {
      creativeData.ad_text = creative.headline;
    }

    if (creative.cta) {
      creativeData.cta_type = creative.cta;
    }

    return creativeData;
  }

  transformUpdateData(updateData) {
    const transformed = {};
    
    if (updateData.status) {
      transformed.status = updateData.status.toUpperCase();
    }
    
    if (updateData.name) {
      transformed.ad_name = updateData.name;
    }

    return transformed;
  }

  mapTikTokStatus(status) {
    const statusMap = {
      'STATUS_DELIVER': 'active',
      'STATUS_PAUSE': 'paused',
      'STATUS_DELETE': 'deleted',
      'STATUS_DRAFT': 'draft'
    };
    return statusMap[status] || 'unknown';
  }

  isRetryableError(error) {
    const retryablePatterns = [
      /rate limit/i,
      /quota/i,
      /timeout/i,
      /network/i,
      /temporary/i,
      /service unavailable/i
    ];

    return retryablePatterns.some(pattern => pattern.test(error.message)) ||
           error.code === 'RATE_LIMIT_EXCEEDED' ||
           error.code === 'INTERNAL_ERROR';
  }
}
