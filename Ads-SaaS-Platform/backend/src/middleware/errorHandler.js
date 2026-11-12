export const errorHandler = async (c, next) => {
  try {
    await next();
  } catch (error) {
    console.error('Error occurred:', error);
    
    // Handle different error types
    if (error.name === 'ValidationError') {
      return c.json({ 
        error: 'Validation Error', 
        details: error.message 
      }, 400);
    }
    
    if (error.name === 'UnauthorizedError') {
      return c.json({ 
        error: 'Unauthorized', 
        details: error.message 
      }, 401);
    }
    
    if (error.name === 'NotFoundError') {
      return c.json({ 
        error: 'Not Found', 
        details: error.message 
      }, 404);
    }
    
    // Default error response
    return c.json({ 
      error: 'Internal Server Error',
      message: c.env.ENVIRONMENT === 'development' ? error.message : 'Something went wrong'
    }, 500);
  }
};
