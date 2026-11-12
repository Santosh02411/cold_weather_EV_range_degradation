import bcrypt from 'bcryptjs';
import { sign } from 'hono/jwt';
// Removed uuid import

export class User {
  constructor(db) {
    this.db = db;
  }

  async create(userData) {
    const { email, password, name } = userData;
    const userId = crypto.randomUUID();
    const passwordHash = await bcrypt.hash(password, 10);

    const stmt = this.db.prepare(`
      INSERT INTO users (id, email, password_hash, name)
      VALUES (?, ?, ?, ?)
    `);

    try {
      await stmt.bind(userId, email || null, passwordHash || null, name || null).run();
      return { id: userId, email, name };
    } catch (error) {
      if (error.message.includes('UNIQUE constraint failed')) {
        throw new Error('Email already exists');
      }
      throw error;
    }
  }

  async findByEmail(email) {
    const stmt = this.db.prepare(`
      SELECT id, email, password_hash, name, created_at, updated_at
      FROM users WHERE email = ?
    `);

    const result = await stmt.bind(email).first();
    return result;
  }

  async findById(userId) {
    const stmt = this.db.prepare(`
      SELECT id, email, name, created_at, updated_at
      FROM users WHERE id = ?
    `);

    const result = await stmt.bind(userId).first();
    return result;
  }

  async verifyPassword(user, password) {
    return bcrypt.compare(password, user.password_hash);
  }

  async generateToken(user, secret) {
    const payload = {
      userId: user.id,
      email: user.email,
      exp: Math.floor(Date.now() / 1000) + 60 * 60 * 24 * 7 // 7 days
    };
    return await sign(payload, 'ads-saas-secret-key');
  }

  async update(userId, userData) {
    const { email } = userData;
    const stmt = this.db.prepare(`
      UPDATE users 
      SET email = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);

    await stmt.bind(email, userId).run();
    return this.findById(userId);
  }

  async delete(userId) {
    const stmt = this.db.prepare(`DELETE FROM users WHERE id = ?`);
    await stmt.bind(userId).run();
  }
}
