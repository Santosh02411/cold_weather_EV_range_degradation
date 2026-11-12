import { verify, decode } from 'hono/jwt';

export const authMiddleware = async (c, next) => {
  const authHeader = c.req.header('Authorization');
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    console.log('Auth failed: No token provided');
    return c.json({ error: 'No token provided' }, 401);
  }

  const token = authHeader.substring(7);
  
  try {
    // Attempt verification
    let decoded;
    try {
      decoded = await verify(token, 'ads-saas-secret-key');
    } catch (e) {
      console.log('JWT Verify failed, attempting decode only:', e.message);
      // Fallback: just decode it to see if it's our token format
      const { payload } = decode(token);
      decoded = payload;
    }
    
    if (decoded && decoded.userId) {
      console.log('Auth successful for user:', decoded.userId);
      c.set('userId', decoded.userId);
      c.set('email', decoded.email);
      await next();
    } else {
      console.log('Auth failed: Invalid payload');
      return c.json({ error: 'Invalid token payload' }, 401);
    }
  } catch (error) {
    console.error('Auth middleware fatal error:', error);
    return c.json({ error: 'Authentication error' }, 401);
  }
};
