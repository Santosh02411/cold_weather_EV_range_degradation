'use client'

import { useState, useEffect } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import type { Platform } from '@/types'
import {
  PlusIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  Cog6ToothIcon,
  LinkIcon,
  TrashIcon
} from '@heroicons/react/24/outline'

export default function IntegrationsPage() {
  const [platforms, setPlatforms] = useState<Platform[]>([])
  const [loading, setLoading] = useState(true)
  const [showConnectModal, setShowConnectModal] = useState(false)
  const [selectedPlatform, setSelectedPlatform] = useState<string>('')

  useEffect(() => {
    fetchPlatforms()
  }, [])

  const fetchPlatforms = async () => {
    try {
      const response = await api.get('/api/platforms')
      setPlatforms(response.data.platforms || [])
    } catch (error) {
      console.error('Failed to fetch platforms:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleConnect = async (platformType: string) => {
    setSelectedPlatform(platformType)
    
    try {
      // Find the platform by type
      let platform = platforms.find(p => p.type === platformType)
      
      // If platform integration doesn't exist yet, create it
      if (!platform) {
        const platformInfo = platformTypes.find(p => p.type === platformType)
        const response = await api.post('/api/platforms', {
          name: platformInfo?.name || platformType,
          type: platformType,
          config: {}
        })
        platform = response.data.platform
      }

      if (!platform) {
        toast.error('Failed to initialize platform')
        return
      }
      
      // Auto-connect with default credentials using platform ID
      const connectResponse = await api.post(`/api/platforms/${platform.id}/connect`, {
        access_token: 'demo-token',
        account_id: 'demo-account',
        app_id: 'demo-app', // For TikTok
        client_id: 'demo-client', // For Google
        client_secret: 'demo-secret', // For Google
        developer_token: 'demo-dev-token' // For Google
      })
      const updatedPlatform = connectResponse.data.platform
      
      toast.success(`${platformTypes.find(p => p.type === platformType)?.name} connected successfully!`)
      
      // Refetch platforms to ensure UI updates
      await fetchPlatforms()
    } catch (error: any) {
      console.error('Failed to connect platform:', error)
      toast.error(error.response?.data?.error || 'Failed to connect platform')
    }
  }

  const handleConnectSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      // Send default credentials automatically
      const response = await api.post(`/api/platforms/${selectedPlatform}/connect`, {
        access_token: 'demo-token',
        account_id: 'demo-account'
      })
      const updatedPlatform = response.data.platform
      
      // Update platforms state
      setPlatforms(prev => 
        prev.map(p => p.type === selectedPlatform ? updatedPlatform : p)
      )
      
      setShowConnectModal(false)
      setSelectedPlatform('')
      toast.success(`${platformTypes.find(p => p.type === selectedPlatform)?.name} connected successfully!`)
      
      // Refetch platforms to ensure UI updates
      await fetchPlatforms()
    } catch (error: any) {
      console.error('Failed to connect platform:', error)
      toast.error(error.response?.data?.error || 'Failed to connect platform')
    }
  }

  const handleDisconnect = async (platformId: string) => {
    if (!confirm('Are you sure you want to disconnect this platform?')) return

    try {
      await api.post(`/api/platforms/${platformId}/disconnect`)
      await fetchPlatforms()
    } catch (error) {
      console.error('Failed to disconnect platform:', error)
    }
  }

  const handleDelete = async (platformId: string) => {
    if (!confirm('Are you sure you want to delete this platform integration?')) return

    try {
      await api.delete(`/api/platforms/${platformId}`)
      await fetchPlatforms()
    } catch (error) {
      console.error('Failed to delete platform:', error)
    }
  }

  const platformTypes = [
    {
      type: 'facebook',
      name: 'Facebook Ads',
      description: 'Reach users on Facebook and Instagram',
      icon: '📘',
      color: 'bg-blue-500'
    },
    {
      type: 'google',
      name: 'Google Ads',
      description: 'Reach users across Google Search and Display Network',
      icon: '🔍',
      color: 'bg-green-500'
    },
    {
      type: 'tiktok',
      name: 'TikTok Ads',
      description: 'Reach users on TikTok',
      icon: '🎵',
      color: 'bg-black'
    },
    {
      type: 'instagram',
      name: 'Instagram Business',
      description: 'Reach users on Instagram',
      icon: '📷',
      color: 'bg-pink-500'
    }
  ]

  const getStatusIcon = (isConnected: boolean) => {
    return isConnected ? (
      <CheckCircleIcon className="h-5 w-5 text-green-500" />
    ) : (
      <XCircleIcon className="h-5 w-5 text-gray-400" />
    )
  }

  const getStatusBadge = (isConnected: boolean) => {
    return `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
      isConnected 
        ? 'bg-green-100 text-green-800' 
        : 'bg-gray-100 text-gray-800'
    }`
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white p-6 rounded-lg shadow">
                <div className="h-6 bg-gray-200 rounded mb-4"></div>
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Integrations</h1>
          <p className="mt-2 text-gray-600">Connect your social media advertising platforms.</p>
        </div>

        {/* Available Platforms */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Available Platforms</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {platformTypes.map((platform) => {
              const isConnected = platforms.some(p => p.type === platform.type && p.is_connected)
              const hasIntegration = platforms.some(p => p.type === platform.type)
              
              return (
                <div key={platform.type} className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <span className="text-2xl mr-3">{platform.icon}</span>
                      <div>
                        <h3 className="font-medium text-gray-900">{platform.name}</h3>
                        <p className="text-sm text-gray-500">{platform.description}</p>
                      </div>
                    </div>
                    {getStatusIcon(isConnected)}
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className={getStatusBadge(isConnected)}>
                      {isConnected ? 'Connected' : hasIntegration ? 'Disconnected' : 'Not Connected'}
                    </span>
                    
                    {!isConnected ? (
                      <button
                        onClick={() => handleConnect(platform.type)}
                        className="btn-primary text-sm"
                      >
                        <LinkIcon className="h-4 w-4 mr-1" />
                        {hasIntegration ? 'Reconnect' : 'Connect'}
                      </button>
                    ) : (
                      <button className="btn-outline text-sm">
                        <Cog6ToothIcon className="h-4 w-4 mr-1" />
                        Configure
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Connected Platforms */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Integrations</h2>
          
          {platforms.length > 0 ? (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {platforms.map((platform) => {
                  const platformInfo = platformTypes.find(p => p.type === platform.type)
                  
                  return (
                    <li key={platform.id}>
                      <div className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <span className="text-2xl mr-3">{platformInfo?.icon}</span>
                            <div>
                              <h3 className="text-lg font-medium text-gray-900">{platform.name}</h3>
                              <p className="text-sm text-gray-500 capitalize">{platform.type}</p>
                              <p className="text-xs text-gray-400 mt-1">
                                Connected: {platform.is_connected ? 'Yes' : 'No'}
                              </p>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            {platform.is_connected && (
                              <button className="p-2 text-blue-600 hover:text-blue-800" title="Configure">
                                <Cog6ToothIcon className="h-5 w-5" />
                              </button>
                            )}
                            
                            {platform.is_connected ? (
                              <button
                                onClick={() => handleDisconnect(platform.id)}
                                className="p-2 text-yellow-600 hover:text-yellow-800"
                                title="Disconnect"
                              >
                                <XCircleIcon className="h-5 w-5" />
                              </button>
                            ) : (
                              <button
                                onClick={() => handleConnect(platform.type)}
                                className="p-2 text-green-600 hover:text-green-800"
                                title="Connect"
                              >
                                <LinkIcon className="h-5 w-5" />
                              </button>
                            )}
                            
                            <button
                              onClick={() => handleDelete(platform.id)}
                              className="p-2 text-red-600 hover:text-red-800"
                              title="Delete Integration"
                            >
                              <TrashIcon className="h-5 w-5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          ) : (
            <div className="bg-white p-12 rounded-lg shadow text-center">
              <ExclamationTriangleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No integrations yet</h3>
              <p className="text-gray-500 mb-4">
                Connect your first social media platform to start creating campaigns.
              </p>
              <button
                onClick={() => handleConnect('facebook')}
                className="btn-primary"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Add Platform
              </button>
            </div>
          )}
        </div>

        {/* Connect Modal */}
        {showConnectModal && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" onClick={() => setShowConnectModal(false)}>
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="sm:flex sm:items-start">
                    <div className="w-full">
                      <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                        Connect {platformTypes.find(p => p.type === selectedPlatform)?.name}
                      </h3>
                      
                      <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
                        <div className="flex">
                          <div className="flex-shrink-0">
                            <ExclamationTriangleIcon className="h-5 w-5 text-blue-400" />
                          </div>
                          <div className="ml-3">
                            <h3 className="text-sm font-medium text-blue-800">
                              Connection Instructions
                            </h3>
                            <div className="mt-2 text-sm text-blue-700">
                              <p>To connect this platform, you'll need to:</p>
                              <ol className="list-decimal list-inside mt-2 space-y-1">
                                <li>Get your API credentials from the platform</li>
                                <li>Enter your access token and account ID</li>
                                <li>Grant permission to manage ads</li>
                              </ol>
                            </div>
                          </div>
                        </div>
                      </div>

                      <form onSubmit={handleConnectSubmit} className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Access Token
                          </label>
                          <input
                            type="password"
                            className="input"
                            placeholder="Enter your access token (or use 'demo-token')"
                            defaultValue="demo-token"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Account ID
                          </label>
                          <input
                            type="text"
                            className="input"
                            placeholder="Enter your account ID (or use 'demo-account')"
                            defaultValue="demo-account"
                            required
                          />
                        </div>

                        <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
                          <p className="text-sm text-blue-700">
                            💡 <strong>Demo Credentials:</strong> Use "demo-token" and "demo-account" for quick testing
                          </p>
                        </div>
                      </form>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="button"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
                    onClick={() => setShowConnectModal(false)}
                  >
                    Connect Platform
                  </button>
                  <button
                    type="button"
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                    onClick={() => setShowConnectModal(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
