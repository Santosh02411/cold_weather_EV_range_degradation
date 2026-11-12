import { Hono } from 'hono';
import { User } from '../models/User.js';
import { Log } from '../models/Log.js';

const auth = new Hono();

// Register endpoint
auth.post('/register', async (c) => {
  try {
    const { email, password, name } = await c.req.json();
    
    if (!email || !password) {
      return c.json({ error: 'Email and password are required' }, 400);
    }

    if (password.length < 6) {
      return c.json({ error: 'Password must be at least 6 characters' }, 400);
    }

    const user = new User(c.env.DB);
    const log = new Log(c.env.DB);

    const existingUser = await user.findByEmail(email);
    if (existingUser) {
      return c.json({ error: 'Email already exists' }, 409);
    }

    const newUser = await user.create({ email, password, name });
    
    await log.info('User registered successfully', { userId: newUser.id }, newUser.id);

    const token = await user.generateToken(newUser, c.env.JWT_SECRET);

    return c.json({
      user: {
        id: newUser.id,
        email: newUser.email,
        name: newUser.name
      },
      token
    }, 201);
  } catch (error) {
    console.error('Registration error:', error);
    return c.json({ error: 'Registration failed' }, 500);
  }
});

// Login endpoint
auth.post('/login', async (c) => {
  try {
    const { email, password } = await c.req.json();
    
    if (!email || !password) {
      return c.json({ error: 'Email and password are required' }, 400);
    }

    const user = new User(c.env.DB);
    const log = new Log(c.env.DB);

    const foundUser = await user.findByEmail(email);
    if (!foundUser) {
      return c.json({ error: 'Invalid credentials' }, 401);
    }

    const isValidPassword = await user.verifyPassword(foundUser, password);
    if (!isValidPassword) {
      return c.json({ error: 'Invalid credentials' }, 401);
    }

    // Store session in KV
    const sessionData = {
      userId: foundUser.id,
      email: foundUser.email,
      loginTime: new Date().toISOString()
    };
    
    await c.env.SESSIONS.put(`session:${foundUser.id}`, JSON.stringify(sessionData), {
      expirationTtl: 7 * 24 * 60 * 60 // 7 days
    });

    await log.info('User logged in successfully', { userId: foundUser.id }, foundUser.id);

    const token = await user.generateToken(foundUser, c.env.JWT_SECRET);

    return c.json({
      user: {
        id: foundUser.id,
        email: foundUser.email,
        name: foundUser.name
      },
      token
    });
  } catch (error) {
    console.error('Login error:', error);
    return c.json({ error: 'Login failed' }, 500);
  }
});

// Logout endpoint
auth.post('/logout', async (c) => {
  try {
    const userId = c.get('userId');
    
    if (userId) {
      // Remove session from KV
      await c.env.SESSIONS.delete(`session:${userId}`);
      
      const log = new Log(c.env.DB);
      await log.info('User logged out', { userId }, userId);
    }

    return c.json({ message: 'Logged out successfully' });
  } catch (error) {
    console.error('Logout error:', error);
    return c.json({ error: 'Logout failed' }, 500);
  }
});

// Get current user
auth.get('/me', async (c) => {
  try {
    const userId = c.get('userId');
    const email = c.get('email');

    if (!userId) {
      return c.json({ error: 'Not authenticated' }, 401);
    }

    return c.json({
      user: {
        id: userId,
        email: email,
        name: c.get('name')
      }
    });
  } catch (error) {
    console.error('Get user error:', error);
    return c.json({ error: 'Failed to get user info' }, 500);
  }
});

// Refresh token endpoint
auth.post('/refresh', async (c) => {
  try {
    const userId = c.get('userId');
    
    if (!userId) {
      return c.json({ error: 'Not authenticated' }, 401);
    }

    const user = new User(c.env.DB);
    const foundUser = await user.findById(userId);
    
    if (!foundUser) {
      return c.json({ error: 'User not found' }, 404);
    }

    const token = await user.generateToken(foundUser, c.env.JWT_SECRET);

    return c.json({ token });
  } catch (error) {
    console.error('Token refresh error:', error);
    return c.json({ error: 'Token refresh failed' }, 500);
  }
});

export { auth as authRoutes };
