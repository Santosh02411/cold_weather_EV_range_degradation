// Removed uuid import

export class Platform {
  constructor(db) {
    this.db = db;
  }

  async create(platformData, userId) {
    const { name, type, config } = platformData;
    const platformId = crypto.randomUUID();

    const stmt = this.db.prepare(`
      INSERT INTO platforms (id, name, type, config, user_id)
      VALUES (?, ?, ?, ?, ?)
    `);

    await stmt.bind(
      platformId,
      name || null,
      type || null,
      JSON.stringify(config || {}),
      userId || null
    ).run();

    return this.findById(platformId);
  }

  async findById(platformId) {
    const stmt = this.db.prepare(`
      SELECT id, name, type, config, user_id, is_connected, created_at, updated_at
      FROM platforms WHERE id = ?
    `);

    const result = await stmt.bind(platformId).first();
    
    if (result && result.config) {
      result.config = JSON.parse(result.config);
    }
    
    return result;
  }

  async findByUserId(userId) {
    const stmt = this.db.prepare(`
      SELECT id, name, type, config, user_id, is_connected, created_at, updated_at
      FROM platforms WHERE user_id = ?
      ORDER BY created_at DESC
    `);

    const results = await stmt.bind(userId).all();
    
    return results.map(platform => ({
      ...platform,
      config: platform.config ? JSON.parse(platform.config) : {}
    }));
  }

  async update(platformId, updateData) {
    const { name, config, isConnected } = updateData;
    
    const stmt = this.db.prepare(`
      UPDATE platforms 
      SET name = ?, config = ?, is_connected = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);

    await stmt.bind(
      name,
      JSON.stringify(config || {}),
      isConnected || false,
      platformId
    ).run();

    return this.findById(platformId);
  }

  async delete(platformId) {
    const stmt = this.db.prepare(`DELETE FROM platforms WHERE id = ?`);
    await stmt.bind(platformId).run();
  }

  async connect(platformId, credentials) {
    // This would typically validate credentials with the actual platform
    // For now, we'll just mark it as connected
    const platform = await this.findById(platformId);
    if (!platform) {
      throw new Error('Platform not found');
    }

    const updatedConfig = {
      ...platform.config,
      ...credentials,
      connectedAt: new Date().toISOString()
    };

    return await this.update(platformId, {
      name: platform.name,
      config: updatedConfig,
      isConnected: true
    });
  }

  async disconnect(platformId) {
    const platform = await this.findById(platformId);
    if (!platform) {
      throw new Error('Platform not found');
    }

    const updatedConfig = {
      ...platform.config,
      disconnectedAt: new Date().toISOString()
    };

    return await this.update(platformId, {
      name: platform.name,
      config: updatedConfig,
      isConnected: false
    });
  }

  async getConnectedPlatforms(userId) {
    const stmt = this.db.prepare(`
      SELECT id, name, type, config, user_id, is_connected, created_at, updated_at
      FROM platforms 
      WHERE user_id = ? AND is_connected = TRUE
      ORDER BY created_at DESC
    `);

    const results = await stmt.bind(userId).all();
    
    return results.map(platform => ({
      ...platform,
      config: platform.config ? JSON.parse(platform.config) : {}
    }));
  }

  async getByType(type, userId) {
    const stmt = this.db.prepare(`
      SELECT id, name, type, config, user_id, is_connected, created_at, updated_at
      FROM platforms 
      WHERE type = ? AND user_id = ?
      ORDER BY created_at DESC
    `);

    const results = await stmt.bind(type, userId).all();
    
    return results.map(platform => ({
      ...platform,
      config: platform.config ? JSON.parse(platform.config) : {}
    }));
  }
}
