import { Hono } from 'hono';
import { Platform } from '../models/Platform.js';
import { Log } from '../models/Log.js';

const platforms = new Hono();

// Get all platforms for user
platforms.get('/', async (c) => {
  try {
    const userId = c.get('userId');

    const platform = new Platform(c.env.DB);
    const userPlatforms = await platform.findByUserId(userId);

    return c.json({ platforms: userPlatforms });
  } catch (error) {
    console.error('Get platforms error:', error);
    return c.json({ error: 'Failed to get platforms' }, 500);
  }
});

// Get connected platforms
platforms.get('/connected', async (c) => {
  try {
    const userId = c.get('userId');

    const platform = new Platform(c.env.DB);
    const connectedPlatforms = await platform.getConnectedPlatforms(userId);

    return c.json({ platforms: connectedPlatforms });
  } catch (error) {
    console.error('Get connected platforms error:', error);
    return c.json({ error: 'Failed to get connected platforms' }, 500);
  }
});

// Get single platform
platforms.get('/:id', async (c) => {
  try {
    const userId = c.get('userId');
    const platformId = c.req.param('id');

    const platform = new Platform(c.env.DB);
    const foundPlatform = await platform.findById(platformId);

    if (!foundPlatform) {
      return c.json({ error: 'Platform not found' }, 404);
    }

    if (foundPlatform.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    return c.json({ platform: foundPlatform });
  } catch (error) {
    console.error('Get platform error:', error);
    return c.json({ error: 'Failed to get platform' }, 500);
  }
});

// Create new platform
platforms.post('/', async (c) => {
  try {
    const userId = c.get('userId');
    console.log('User ID from context:', userId);
    const platformData = await c.req.json();

    // Validate required fields
    const { name, type, config } = platformData;
    if (!name || !type) {
      return c.json({ error: 'Name and type are required' }, 400);
    }

    const validTypes = ['facebook', 'google', 'tiktok', 'instagram'];
    if (!validTypes.includes(type)) {
      return c.json({ error: 'Invalid platform type' }, 400);
    }

    const platform = new Platform(c.env.DB);
    const log = new Log(c.env.DB);

    const newPlatform = await platform.create(platformData, userId);

    await log.info('Platform created', { 
      platformId: newPlatform.id,
      name: newPlatform.name,
      type: newPlatform.type
    }, userId, null, newPlatform.id);

    return c.json({ platform: newPlatform }, 201);
  } catch (error) {
    console.error('Create platform error:', error);
    return c.json({ 
      error: 'Failed to create platform',
      message: error.message 
    }, 500);
  }
});

// Update platform
platforms.put('/:id', async (c) => {
  try {
    const userId = c.get('userId');
    const platformId = c.req.param('id');
    const updateData = await c.req.json();

    const platform = new Platform(c.env.DB);
    const existingPlatform = await platform.findById(platformId);

    if (!existingPlatform) {
      return c.json({ error: 'Platform not found' }, 404);
    }

    if (existingPlatform.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    const updatedPlatform = await platform.update(platformId, updateData);

    const log = new Log(c.env.DB);
    await log.info('Platform updated', { 
      platformId: platformId,
      updates: Object.keys(updateData)
    }, userId, null, platformId);

    return c.json({ platform: updatedPlatform });
  } catch (error) {
    console.error('Update platform error:', error);
    return c.json({ error: 'Failed to update platform' }, 500);
  }
});

// Delete platform
platforms.delete('/:id', async (c) => {
  try {
    const userId = c.get('userId');
    const platformId = c.req.param('id');

    const platform = new Platform(c.env.DB);
    const existingPlatform = await platform.findById(platformId);

    if (!existingPlatform) {
      return c.json({ error: 'Platform not found' }, 404);
    }

    if (existingPlatform.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    await platform.delete(platformId);

    const log = new Log(c.env.DB);
    await log.info('Platform deleted', { 
      platformId: platformId,
      name: existingPlatform.name,
      type: existingPlatform.type
    }, userId);

    return c.json({ message: 'Platform deleted successfully' });
  } catch (error) {
    console.error('Delete platform error:', error);
    return c.json({ error: 'Failed to delete platform' }, 500);
  }
});

// Connect platform
platforms.post('/:id/connect', async (c) => {
  try {
    const userId = c.get('userId');
    const platformId = c.req.param('id');
    const credentials = await c.req.json();

    const platform = new Platform(c.env.DB);
    const existingPlatform = await platform.findById(platformId);

    if (!existingPlatform) {
      return c.json({ error: 'Platform not found' }, 404);
    }

    if (existingPlatform.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    // Validate credentials based on platform type
    const validationError = await validatePlatformCredentials(existingPlatform.type, credentials);
    if (validationError) {
      return c.json({ error: validationError }, 400);
    }

    const connectedPlatform = await platform.connect(platformId, credentials);

    const log = new Log(c.env.DB);
    await log.info('Platform connected', { 
      platformId: platformId,
      platformType: existingPlatform.type
    }, userId, null, platformId);

    return c.json({ platform: connectedPlatform });
  } catch (error) {
    console.error('Connect platform error:', error);
    return c.json({ 
      error: 'Failed to connect platform',
      message: error.message 
    }, 500);
  }
});

// Disconnect platform
platforms.post('/:id/disconnect', async (c) => {
  try {
    const userId = c.get('userId');
    const platformId = c.req.param('id');

    const platform = new Platform(c.env.DB);
    const existingPlatform = await platform.findById(platformId);

    if (!existingPlatform) {
      return c.json({ error: 'Platform not found' }, 404);
    }

    if (existingPlatform.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    const disconnectedPlatform = await platform.disconnect(platformId);

    const log = new Log(c.env.DB);
    await log.info('Platform disconnected', { 
      platformId: platformId,
      platformType: existingPlatform.type
    }, userId, null, platformId);

    return c.json({ platform: disconnectedPlatform });
  } catch (error) {
    console.error('Disconnect platform error:', error);
    return c.json({ error: 'Failed to disconnect platform' }, 500);
  }
});

// Test platform connection
platforms.post('/:id/test', async (c) => {
  try {
    const userId = c.get('userId');
    const platformId = c.req.param('id');

    const platform = new Platform(c.env.DB);
    const existingPlatform = await platform.findById(platformId);

    if (!existingPlatform) {
      return c.json({ error: 'Platform not found' }, 404);
    }

    if (existingPlatform.user_id !== userId) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    if (!existingPlatform.is_connected) {
      return c.json({ error: 'Platform is not connected' }, 400);
    }

    // Test connection (mock implementation)
    const testResult = await testPlatformConnection(existingPlatform);

    const log = new Log(c.env.DB);
    await log.info('Platform connection tested', { 
      platformId: platformId,
      success: testResult.success
    }, userId, null, platformId);

    return c.json({ 
      success: testResult.success,
      message: testResult.message
    });
  } catch (error) {
    console.error('Test platform connection error:', error);
    return c.json({ error: 'Failed to test platform connection' }, 500);
  }
});

// Helper functions
async function validatePlatformCredentials(type, credentials) {
  switch (type) {
    case 'facebook':
      if (!credentials.accessToken || !credentials.accountId) {
        return 'Access token and account ID are required for Facebook';
      }
      break;
    case 'google':
      if (!credentials.clientId || !credentials.clientSecret || !credentials.developerToken) {
        return 'Client ID, client secret, and developer token are required for Google Ads';
      }
      break;
    case 'tiktok':
      if (!credentials.accessToken || !credentials.appId) {
        return 'Access token and app ID are required for TikTok Ads';
      }
      break;
    case 'instagram':
      if (!credentials.accessToken || !credentials.businessAccountId) {
        return 'Access token and business account ID are required for Instagram';
      }
      break;
    default:
      return 'Unknown platform type';
  }
  
  return null;
}

async function testPlatformConnection(platform) {
  // Mock implementation - in real app, this would make actual API calls
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Randomly succeed or fail for demo purposes
    const success = Math.random() > 0.2; // 80% success rate
    
    return {
      success,
      message: success ? 'Connection successful' : 'Connection failed: Invalid credentials'
    };
  } catch (error) {
    return {
      success: false,
      message: `Connection failed: ${error.message}`
    };
  }
}

export { platforms as platformRoutes };
