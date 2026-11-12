import { BaseAdapter } from '../BaseAdapter.js';

export class GoogleAdapter extends BaseAdapter {
  constructor(config) {
    super(config);
    this.apiVersion = 'v11';
    this.baseUrl = 'https://googleads.googleapis.com';
    this.developerToken = config.developerToken;
  }

  async connectPlatform(credentials) {
    try {
      const { clientId, clientSecret, refreshToken, managerAccountId } = credentials;
      
      // Validate credentials by getting access token
      const accessToken = await this.getAccessToken(refreshToken, clientId, clientSecret);
      
      if (!accessToken) {
        throw new Error('Invalid credentials');
      }

      // Test account access
      const customerResponse = await this.makeApiRequest(
        `customers/${managerAccountId}`,
        'GET',
        null,
        accessToken
      );

      this.config.accessToken = accessToken;
      this.config.clientId = clientId;
      this.config.clientSecret = clientSecret;
      this.config.refreshToken = refreshToken;
      this.config.managerAccountId = managerAccountId;
      this.config.connectedAt = new Date().toISOString();

      this.log('info', 'Successfully connected to Google Ads', {
        managerAccountId,
        customerName: customerResponse.customer?.descriptiveName
      });

      return {
        success: true,
        platformId: this.config.id,
        externalAccountId: managerAccountId,
        accountName: customerResponse.customer?.descriptiveName || 'Google Ads Account'
      };
    } catch (error) {
      this.log('error', 'Failed to connect to Google Ads', { error: error.message });
      throw this.handleError(error);
    }
  }

  async publishAd(adData) {
    try {
      const { campaign, creative, targeting, budget } = adData;
      const accessToken = await this.getAccessToken();
      
      // Step 1: Create campaign budget
      const budgetData = {
        name: `${campaign.title} - Budget`,
        amountMicros: budget * 1000000, // Convert to micros
        deliveryMethod: 'STANDARD'
      };

      const budgetResponse = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/campaignBudgets:create`,
        'POST',
        { campaignBudget: budgetData },
        accessToken
      );

      // Step 2: Create campaign
      const campaignData = this.transformCampaignData({
        name: campaign.title,
        advertisingChannelType: 'SEARCH',
        campaignBudget: budgetResponse.results[0].resourceName,
        targetCpa: { micros: 1000000 }, // $1.00 CPA
        status: 'PAUSED'
      });

      const campaignResponse = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/campaigns:create`,
        'POST',
        { campaign: campaignData },
        accessToken
      );

      // Step 3: Create ad group
      const adGroupData = {
        name: `${campaign.title} - Ad Group`,
        campaign: campaignResponse.results[0].resourceName,
        status: 'PAUSED'
      };

      const adGroupResponse = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/adGroups:create`,
        'POST',
        { adGroup: adGroupData },
        accessToken
      );

      // Step 4: Create ad
      const adData = await this.transformCreative(creative);
      const adResponse = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/ads:create`,
        'POST',
        { ad: adData },
        accessToken
      );

      // Step 5: Set targeting
      if (targeting) {
        await this.setTargeting(
          adGroupResponse.results[0].resourceName,
          targeting,
          accessToken
        );
      }

      this.log('info', 'Successfully published Google Ads campaign', {
        campaignId: campaignResponse.results[0].resourceName,
        adGroupId: adGroupResponse.results[0].resourceName,
        adId: adResponse.results[0].resourceName
      });

      return {
        success: true,
        externalId: campaignResponse.results[0].resourceName,
        campaignId: campaignResponse.results[0].resourceName,
        adGroupId: adGroupResponse.results[0].resourceName,
        adId: adResponse.results[0].resourceName,
        budgetId: budgetResponse.results[0].resourceName,
        status: 'published'
      };
    } catch (error) {
      this.log('error', 'Failed to publish Google Ads campaign', { error: error.message });
      throw this.handleError(error);
    }
  }

  async getStatus(externalId) {
    try {
      const accessToken = await this.getAccessToken();
      
      const response = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/googleAdsFields:search`,
        'POST',
        {
          query: `
            SELECT campaign.id, campaign.name, campaign.status 
            FROM campaign 
            WHERE campaign.resource_name = '${externalId}'
          `
        },
        accessToken
      );

      const campaign = response.results?.[0];
      
      return {
        success: true,
        status: this.mapGoogleStatus(campaign?.campaign?.status),
        campaignName: campaign?.campaign?.name,
        lastUpdated: new Date().toISOString()
      };
    } catch (error) {
      this.log('error', 'Failed to get Google Ads status', { 
        externalId, 
        error: error.message 
      });
      throw this.handleError(error);
    }
  }

  async updateAd(externalId, updateData) {
    try {
      const accessToken = await this.getAccessToken();
      const updates = this.transformUpdateData(updateData);
      
      const response = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/campaigns:update`,
        'POST',
        { campaign: updates },
        accessToken
      );

      this.log('info', 'Successfully updated Google Ads campaign', { externalId });

      return {
        success: true,
        externalId,
        updatedFields: Object.keys(updateData)
      };
    } catch (error) {
      this.log('error', 'Failed to update Google Ads campaign', { 
        externalId, 
        error: error.message 
      });
      throw this.handleError(error);
    }
  }

  async deleteAd(externalId) {
    try {
      const accessToken = await this.getAccessToken();
      
      await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/campaigns:update`,
        'POST',
        {
          campaign: {
            resourceName: externalId,
            status: 'REMOVED'
          }
        },
        accessToken
      );

      this.log('info', 'Successfully deleted Google Ads campaign', { externalId });

      return {
        success: true,
        externalId
      };
    } catch (error) {
      this.log('error', 'Failed to delete Google Ads campaign', { 
        externalId, 
        error: error.message 
      });
      throw this.handleError(error);
    }
  }

  async getAnalytics(filters = {}) {
    try {
      const accessToken = await this.getAccessToken();
      const { 
        dateRange = 'LAST_7_DAYS', 
        metrics = ['impressions', 'clicks', 'cost'] 
      } = filters;
      
      const query = `
        SELECT campaign.id, campaign.name, ${metrics.join(', ')}
        FROM campaign 
        WHERE segments.date DURING ${dateRange}
      `;

      const response = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/googleAdsFields:search`,
        'POST',
        { query },
        accessToken
      );

      return {
        success: true,
        data: response.results || [],
        metrics
      };
    } catch (error) {
      this.log('error', 'Failed to get Google Ads analytics', { error: error.message });
      throw this.handleError(error);
    }
  }

  async validateCredentials(credentials) {
    try {
      const { clientId, clientSecret, refreshToken } = credentials;
      const accessToken = await this.getAccessToken(refreshToken, clientId, clientSecret);
      return !!accessToken;
    } catch (error) {
      return false;
    }
  }

  getSupportedAdFormats() {
    return ['text', 'image', 'video', 'responsive_search', 'responsive_display'];
  }

  getTargetingOptions() {
    return [
      'age',
      'gender',
      'location',
      'interests',
      'topics',
      'placements',
      'keywords',
      'devices',
      'audiences'
    ];
  }

  // Helper methods
  async getAccessToken(refreshToken = null, clientId = null, clientSecret = null) {
    // Simulate token generation - in production, this would make real OAuth calls
    await new Promise(resolve => setTimeout(resolve, 100));
    return 'mock_access_token_' + Math.random().toString(36).substr(2, 9);
  }

  async makeApiRequest(endpoint, method = 'GET', data = null, accessToken = null) {
    const token = accessToken || await this.getAccessToken();
    const url = `${this.baseUrl}/${this.apiVersion}/${endpoint}`;
    const headers = {
      'Authorization': `Bearer ${token}`,
      'developer-token': this.developerToken,
      'Content-Type': 'application/json'
    };

    let options = { headers, method };

    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }

    // Simulate API call for demo
    await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));

    // Mock response - in production, this would be a real fetch call
    if (endpoint.includes('customers/') && endpoint.includes('/campaignBudgets:create')) {
      return {
        results: [{
          resourceName: `customers/${this.config.managerAccountId}/campaignBudgets/${Math.random().toString(36).substr(2, 9)}`
        }]
      };
    } else if (endpoint.includes('/campaigns:create')) {
      return {
        results: [{
          resourceName: `customers/${this.config.managerAccountId}/campaigns/${Math.random().toString(36).substr(2, 9)}`
        }]
      };
    } else if (endpoint.includes('/adGroups:create')) {
      return {
        results: [{
          resourceName: `customers/${this.config.managerAccountId}/adGroups/${Math.random().toString(36).substr(2, 9)}`
        }]
      };
    } else if (endpoint.includes('/ads:create')) {
      return {
        results: [{
          resourceName: `customers/${this.config.managerAccountId}/ads/${Math.random().toString(36).substr(2, 9)}`
        }]
      };
    } else if (endpoint.includes('googleAdsFields:search')) {
      return {
        results: [
          { campaign: { id: '123456789', name: 'Test Campaign', status: 'ENABLED' } }
        ]
      };
    } else {
      return { success: true };
    }
  }

  transformCampaignData(campaignData) {
    return {
      ...campaignData,
      advertisingChannelType: 'SEARCH',
      status: 'PAUSED'
    };
  }

  async transformCreative(creative) {
    const adData = {
      name: creative.name || 'Google Ad',
      status: 'PAUSED',
      adServingStatus: 'SERVING'
    };

    if (creative.type === 'text') {
      adData.expandedTextAd = {
        headlines: [{ text: creative.headline || 'Default Headline' }],
        descriptions: [{ text: creative.body || 'Default description' }],
        finalUrls: [creative.url || 'https://example.com']
      };
    } else if (creative.type === 'responsive_search') {
      adData.responsiveSearchAd = {
        headlines: [{ text: creative.headline || 'Default Headline' }],
        descriptions: [{ text: creative.body || 'Default description' }],
        finalUrls: [creative.url || 'https://example.com']
      };
    }

    return adData;
  }

  async setTargeting(adGroupResourceName, targeting, accessToken) {
    const targetingData = {
      adGroupCriterion: [
        {
          adGroup: adGroupResourceName,
          keyword: {
            text: targeting.keywords?.[0] || 'default keyword',
            matchType: 'BROAD'
          }
        }
      ]
    };

    await this.makeApiRequest(
      `customers/${this.config.managerAccountId}/adGroupCriteria:create`,
      'POST',
      targetingData,
      accessToken
    );
  }

  transformUpdateData(updateData) {
    const transformed = {
      resourceName: updateData.resourceName
    };
    
    if (updateData.status) {
      transformed.status = updateData.status.toUpperCase();
    }
    
    if (updateData.name) {
      transformed.name = updateData.name;
    }

    return transformed;
  }

  mapGoogleStatus(status) {
    const statusMap = {
      'ENABLED': 'active',
      'PAUSED': 'paused',
      'REMOVED': 'deleted',
      'UNKNOWN': 'unknown'
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
      /internal server error/i
    ];

    return retryablePatterns.some(pattern => pattern.test(error.message)) ||
           error.code === 'QUOTA_EXCEEDED' ||
           error.code === 'INTERNAL_ERROR';
  }
}
