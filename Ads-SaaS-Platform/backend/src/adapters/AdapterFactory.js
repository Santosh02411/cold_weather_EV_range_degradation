import { FacebookAdapter } from './facebook/FacebookAdapter.js';
import { GoogleAdapter } from './google/GoogleAdapter.js';
import { TikTokAdapter } from './tiktok/TikTokAdapter.js';
import { InstagramAdapter } from './instagram/InstagramAdapter.js';

/**
 * Factory class for creating platform adapters
 * Provides a unified interface for managing multiple social media platforms
 */
export class AdapterFactory {
  constructor() {
    this.adapters = new Map();
    this.registerDefaultAdapters();
  }

  /**
   * Register default platform adapters
   */
  registerDefaultAdapters() {
    this.register('facebook', FacebookAdapter);
    this.register('google', GoogleAdapter);
    this.register('tiktok', TikTokAdapter);
    this.register('instagram', InstagramAdapter);
  }

  /**
   * Register a new adapter type
   * @param {string} type - Platform type
   * @param {Class} AdapterClass - Adapter class
   */
  register(type, AdapterClass) {
    this.adapters.set(type.toLowerCase(), AdapterClass);
  }

  /**
   * Create an adapter instance for a platform
   * @param {string} type - Platform type
   * @param {Object} config - Platform configuration
   * @returns {BaseAdapter} Adapter instance
   */
  create(type, config) {
    const AdapterClass = this.adapters.get(type.toLowerCase());
    
    if (!AdapterClass) {
      throw new Error(`Unsupported platform type: ${type}`);
    }

    return new AdapterClass(config);
  }

  /**
   * Get supported platform types
   * @returns {Array} Array of supported platform types
   */
  getSupportedPlatforms() {
    return Array.from(this.adapters.keys());
  }

  /**
   * Check if a platform type is supported
   * @param {string} type - Platform type
   * @returns {boolean} Whether the platform is supported
   */
  isSupported(type) {
    return this.adapters.has(type.toLowerCase());
  }

  /**
   * Get adapter class for a platform type
   * @param {string} type - Platform type
   * @returns {Class} Adapter class
   */
  getAdapterClass(type) {
    return this.adapters.get(type.toLowerCase());
  }

  /**
   * Create multiple adapters from platform configurations
   * @param {Array} platforms - Array of platform configurations
   * @returns {Map} Map of adapter instances
   */
  createMultiple(platforms) {
    const adapterInstances = new Map();

    for (const platform of platforms) {
      try {
        const adapter = this.create(platform.type, platform);
        adapterInstances.set(platform.id, adapter);
      } catch (error) {
        console.error(`Failed to create adapter for platform ${platform.type}:`, error);
      }
    }

    return adapterInstances;
  }

  /**
   * Validate platform configuration
   * @param {Object} config - Platform configuration
   * @returns {Object} Validation result
   */
  validatePlatformConfig(config) {
    const { type, name, credentials } = config;

    if (!type || !this.isSupported(type)) {
      return {
        valid: false,
        error: `Unsupported platform type: ${type}`
      };
    }

    if (!name || name.trim().length === 0) {
      return {
        valid: false,
        error: 'Platform name is required'
      };
    }

    if (!credentials || Object.keys(credentials).length === 0) {
      return {
        valid: false,
        error: 'Platform credentials are required'
      };
    }

    // Platform-specific validation
    const AdapterClass = this.getAdapterClass(type);
    const tempAdapter = new AdapterClass(config);
    
    // This would validate credentials in a real implementation
    // For now, we'll just check if required fields exist
    const requiredFields = this.getRequiredCredentials(type);
    const missingFields = requiredFields.filter(field => !credentials[field]);

    if (missingFields.length > 0) {
      return {
        valid: false,
        error: `Missing required credentials: ${missingFields.join(', ')}`
      };
    }

    return { valid: true };
  }

  /**
   * Get required credentials for a platform type
   * @param {string} type - Platform type
   * @returns {Array} Array of required credential fields
   */
  getRequiredCredentials(type) {
    const requirements = {
      facebook: ['accessToken', 'accountId'],
      google: ['clientId', 'clientSecret', 'refreshToken', 'developerToken'],
      tiktok: ['accessToken', 'appId'],
      instagram: ['accessToken', 'businessAccountId']
    };

    return requirements[type.toLowerCase()] || [];
  }

  /**
   * Get platform capabilities
   * @param {string} type - Platform type
   * @returns {Object} Platform capabilities
   */
  getPlatformCapabilities(type) {
    if (!this.isSupported(type)) {
      throw new Error(`Unsupported platform type: ${type}`);
    }

    const AdapterClass = this.getAdapterClass(type);
    const tempAdapter = new AdapterClass({});

    return {
      supportedAdFormats: tempAdapter.getSupportedAdFormats(),
      targetingOptions: tempAdapter.getTargetingOptions(),
      rateLimit: tempAdapter.getRateLimitInfo()
    };
  }

  /**
   * Test platform connection
   * @param {Object} config - Platform configuration
   * @returns {Promise<Object>} Connection test result
   */
  async testConnection(config) {
    try {
      const adapter = this.create(config.type, config);
      const result = await adapter.validateCredentials(config.credentials);
      
      return {
        success: result,
        platform: config.type,
        message: result ? 'Connection successful' : 'Connection failed'
      };
    } catch (error) {
      return {
        success: false,
        platform: config.type,
        error: error.message
      };
    }
  }

  /**
   * Connect to a platform
   * @param {Object} config - Platform configuration
   * @returns {Promise<Object>} Connection result
   */
  async connectPlatform(config) {
    const validation = this.validatePlatformConfig(config);
    if (!validation.valid) {
      throw new Error(validation.error);
    }

    const adapter = this.create(config.type, config);
    return await adapter.connectPlatform(config.credentials);
  }

  /**
   * Get platform-specific help/documentation
   * @param {string} type - Platform type
   * @returns {Object} Platform help information
   */
  getPlatformHelp(type) {
    const helpInfo = {
      facebook: {
        name: 'Facebook Ads',
        description: 'Reach users on Facebook and Instagram',
        setupSteps: [
          'Create a Facebook Developer account',
          'Create a Facebook App',
          'Get access token with ads_management permission',
          'Get your Ad Account ID'
        ],
        requiredCredentials: [
          { field: 'accessToken', label: 'Access Token', type: 'string' },
          { field: 'accountId', label: 'Ad Account ID', type: 'string' }
        ]
      },
      google: {
        name: 'Google Ads',
        description: 'Reach users across Google Search and Display Network',
        setupSteps: [
          'Create a Google Cloud project',
          'Enable Google Ads API',
          'Create OAuth2 credentials',
          'Get developer token',
          'Get your manager account ID'
        ],
        requiredCredentials: [
          { field: 'clientId', label: 'Client ID', type: 'string' },
          { field: 'clientSecret', label: 'Client Secret', type: 'string' },
          { field: 'refreshToken', label: 'Refresh Token', type: 'string' },
          { field: 'developerToken', label: 'Developer Token', type: 'string' }
        ]
      },
      tiktok: {
        name: 'TikTok Ads',
        description: 'Reach users on TikTok',
        setupSteps: [
          'Create a TikTok for Business account',
          'Create an app in TikTok Developer Portal',
          'Get access token',
          'Get your App ID'
        ],
        requiredCredentials: [
          { field: 'accessToken', label: 'Access Token', type: 'string' },
          { field: 'appId', label: 'App ID', type: 'string' }
        ]
      },
      instagram: {
        name: 'Instagram Business',
        description: 'Reach users on Instagram',
        setupSteps: [
          'Create a Facebook Business account',
          'Connect your Instagram account',
          'Convert to Instagram Business account',
          'Get access token with instagram_basic permission',
          'Get your Business Account ID'
        ],
        requiredCredentials: [
          { field: 'accessToken', label: 'Access Token', type: 'string' },
          { field: 'businessAccountId', label: 'Business Account ID', type: 'string' }
        ]
      }
    };

    return helpInfo[type.toLowerCase()] || null;
  }
}

// Export singleton instance
export const adapterFactory = new AdapterFactory();
