/**
 * Base Adapter Interface for Social Media Platforms
 * All platform adapters must implement this interface
 */
export class BaseAdapter {
  constructor(config) {
    this.config = config;
    this.name = config.name;
    this.type = config.type;
  }

  /**
   * Connect to the platform
   * @param {Object} credentials - Platform-specific credentials
   * @returns {Promise<Object>} Connection result
   */
  async connectPlatform(credentials) {
    throw new Error('connectPlatform method must be implemented');
  }

  /**
   * Publish an ad to the platform
   * @param {Object} adData - Ad campaign data
   * @returns {Promise<Object>} Publish result
   */
  async publishAd(adData) {
    throw new Error('publishAd method must be implemented');
  }

  /**
   * Get status of an ad/campaign
   * @param {string} externalId - External platform ID
   * @returns {Promise<Object>} Status result
   */
  async getStatus(externalId) {
    throw new Error('getStatus method must be implemented');
  }

  /**
   * Update an existing ad
   * @param {string} externalId - External platform ID
   * @param {Object} updateData - Data to update
   * @returns {Promise<Object>} Update result
   */
  async updateAd(externalId, updateData) {
    throw new Error('updateAd method must be implemented');
  }

  /**
   * Delete an ad
   * @param {string} externalId - External platform ID
   * @returns {Promise<Object>} Delete result
   */
  async deleteAd(externalId) {
    throw new Error('deleteAd method must be implemented');
  }

  /**
   * Get platform analytics
   * @param {Object} filters - Analytics filters
   * @returns {Promise<Object>} Analytics data
   */
  async getAnalytics(filters) {
    throw new Error('getAnalytics method must be implemented');
  }

  /**
   * Validate platform credentials
   * @param {Object} credentials - Platform credentials
   * @returns {Promise<boolean>} Validation result
   */
  async validateCredentials(credentials) {
    throw new Error('validateCredentials method must be implemented');
  }

  /**
   * Get platform-specific ad formats
   * @returns {Array} Supported ad formats
   */
  getSupportedAdFormats() {
    return ['image', 'video', 'text'];
  }

  /**
   * Get platform-specific targeting options
   * @returns {Array} Available targeting options
   */
  getTargetingOptions() {
    return [
      'age',
      'gender',
      'location',
      'interests',
      'behaviors',
      'custom_audiences'
    ];
  }

  /**
   * Transform campaign data to platform-specific format
   * @param {Object} campaignData - Standard campaign data
   * @returns {Object} Platform-specific campaign data
   */
  transformCampaignData(campaignData) {
    // Default implementation - override in specific adapters
    return campaignData;
  }

  /**
   * Handle platform-specific errors
   * @param {Error} error - Platform error
   * @returns {Object} Standardized error response
   */
  handleError(error) {
    return {
      success: false,
      error: error.message,
      code: error.code || 'UNKNOWN_ERROR',
      retryable: this.isRetryableError(error)
    };
  }

  /**
   * Determine if an error is retryable
   * @param {Error} error - Platform error
   * @returns {boolean} Whether error is retryable
   */
  isRetryableError(error) {
    const retryableCodes = [
      'RATE_LIMITED',
      'TEMPORARY_FAILURE',
      'NETWORK_ERROR',
      'TIMEOUT'
    ];

    return retryableCodes.includes(error.code) || 
           error.message.includes('rate limit') ||
           error.message.includes('timeout') ||
           error.message.includes('network');
  }

  /**
   * Get rate limit information
   * @returns {Object} Rate limit info
   */
  getRateLimitInfo() {
    return {
      requestsPerSecond: 10,
      requestsPerHour: 1000,
      resetTime: null
    };
  }

  /**
   * Log platform activity
   * @param {string} level - Log level (info, warn, error)
   * @param {string} message - Log message
   * @param {Object} context - Additional context
   */
  log(level, message, context = {}) {
    console.log(`[${this.name}] ${level.toUpperCase()}: ${message}`, context);
  }
}
