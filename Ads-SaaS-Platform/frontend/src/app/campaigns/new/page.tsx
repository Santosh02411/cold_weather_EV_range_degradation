'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import DashboardLayout from '@/components/DashboardLayout'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import type { Platform, CreateCampaignData } from '@/types'
import {
  ArrowLeftIcon,
  PlusIcon,
  XMarkIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

export default function NewCampaignPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [platforms, setPlatforms] = useState<Platform[]>([])
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([])
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    budget: 100,
    platforms: [],
    objective: 'TRAFFIC',
    scheduleStart: '',
    scheduleEnd: ''
  })

  useEffect(() => {
    fetchPlatforms()
  }, [])

  const fetchPlatforms = async () => {
    try {
      const response = await api.get('/api/platforms/connected')
      setPlatforms(response.data.platforms || [])
    } catch (error) {
      console.error('Failed to fetch platforms:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    console.log('Creating campaign with platforms:', selectedPlatforms)
    console.log('Form data:', formData)

    setLoading(true)

    try {
      const campaignData = {
        ...formData,
        platforms: selectedPlatforms.length > 0 ? selectedPlatforms : ['1'] // Use default platform if none selected
      }
      
      console.log('Sending campaign data:', campaignData)
      
      const response = await api.post('/api/campaigns', campaignData)
      console.log('Campaign created:', response.data)
      
      router.push('/campaigns')
    } catch (error: any) {
      console.error('Failed to create campaign:', error)
      console.error('Error response:', error.response?.data)
      alert(`Failed to create campaign: ${error.response?.data?.error || 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value
    }))
  }

  const togglePlatform = (platformId: string) => {
    setSelectedPlatforms(prev => 
      prev.includes(platformId) 
        ? prev.filter(id => id !== platformId)
        : [...prev, platformId]
    )
  }

  const objectives = [
    { value: 'TRAFFIC', label: 'Website Traffic' },
    { value: 'CONVERSIONS', label: 'Conversions' },
    { value: 'LEADS', label: 'Lead Generation' },
    { value: 'ENGAGEMENT', label: 'Engagement' },
    { value: 'AWARENESS', label: 'Brand Awareness' }
  ]

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeftIcon className="h-5 w-5 mr-2" />
            Back to Campaigns
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Create New Campaign</h1>
          <p className="mt-2 text-gray-600">Set up your advertising campaign across multiple platforms.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Campaign Schedule */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Campaign Schedule</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="scheduleStart" className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  id="scheduleStart"
                  name="scheduleStart"
                  className="input"
                  value={formData.scheduleStart}
                  onChange={handleInputChange}
                />
              </div>

              <div>
                <label htmlFor="scheduleEnd" className="block text-sm font-medium text-gray-700 mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  id="scheduleEnd"
                  name="scheduleEnd"
                  className="input"
                  value={formData.scheduleEnd}
                  onChange={handleInputChange}
                  min={formData.scheduleStart}
                />
              </div>
            </div>
          </div>

          {/* Campaign Details */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Campaign Details</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Campaign Title *
                </label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  required
                  className="input"
                  value={formData.title}
                  onChange={handleInputChange}
                  placeholder="Enter campaign title"
                />
              </div>

              <div>
                <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-2">
                  Budget ($) *
                </label>
                <input
                  type="number"
                  id="budget"
                  name="budget"
                  required
                  min="1"
                  step="0.01"
                  className="input"
                  value={formData.budget}
                  onChange={handleInputChange}
                  placeholder="Enter budget amount"
                />
              </div>
            </div>

            <div className="mt-6">
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                id="description"
                name="description"
                rows={3}
                className="input"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="Describe your campaign (optional)"
              />
            </div>

            <div className="mt-6">
              <label htmlFor="objective" className="block text-sm font-medium text-gray-700 mb-2">
                Campaign Objective
              </label>
              <select
                id="objective"
                name="objective"
                className="input"
                value={formData.objective}
                onChange={handleInputChange}
              >
                {objectives.map(obj => (
                  <option key={obj.value} value={obj.value}>
                    {obj.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          
          {/* Platform Selection */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Platforms</h2>
            
            {platforms.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {platforms.map((platform) => (
                  <div
                    key={platform.id}
                    className={`border-2 rounded-lg p-4 cursor-pointer transition-colors ${
                      selectedPlatforms.includes(platform.id)
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => togglePlatform(platform.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{platform.name}</h3>
                        <p className="text-sm text-gray-500 capitalize">{platform.type}</p>
                      </div>
                      <div className={`h-5 w-5 rounded-full border-2 ${
                        selectedPlatforms.includes(platform.id)
                          ? 'bg-primary-500 border-primary-500'
                          : 'border-gray-300'
                      }`}>
                        {selectedPlatforms.includes(platform.id) && (
                          <CheckCircleIcon className="h-full w-full text-white" />
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-4">No connected platforms found.</p>
                <Link
                  href="/integrations"
                  className="btn-primary"
                >
                  Connect Platforms
                </Link>
              </div>
            )}
            
            {selectedPlatforms.length > 0 && (
              <div className="mt-4">
                <p className="text-sm text-gray-600">
                  {selectedPlatforms.length} platform{selectedPlatforms.length > 1 ? 's' : ''} selected
                </p>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => router.back()}
              className="btn-outline"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating Campaign...
                </>
              ) : (
                <>
                  Create Campaign
                </>
              )}
            </button>
          </div>
        </form>

              </div>
    </DashboardLayout>
  )
}
