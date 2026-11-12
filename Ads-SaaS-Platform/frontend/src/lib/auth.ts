import api from './api'

export interface User {
  id: string
  email: string
  name?: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  email: string
  password: string
  name: string
}

export interface AuthResponse {
  user: User
  token: string
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post('/api/auth/login', credentials)
    const { user, token } = response.data
    
    // Store in localStorage
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    
    return { user, token }
  },

  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    const response = await api.post('/api/auth/register', credentials)
    const { user, token } = response.data
    
    // Store in localStorage
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    
    return { user, token }
  },

  async logout(): Promise<void> {
    try {
      await api.post('/api/auth/logout')
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API call failed:', error)
    } finally {
      // Clear localStorage
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  },

  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await api.get('/api/auth/me')
      return response.data.user
    } catch (error) {
      return null
    }
  },

  async refreshToken(): Promise<string> {
    const response = await api.post('/api/auth/refresh')
    const { token } = response.data
    
    // Update token in localStorage
    localStorage.setItem('token', token)
    
    return token
  },

  isAuthenticated(): boolean {
    const token = localStorage.getItem('token')
    return !!token
  },

  getStoredUser(): User | null {
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  },

  getStoredToken(): string | null {
    return localStorage.getItem('token')
  }
}
