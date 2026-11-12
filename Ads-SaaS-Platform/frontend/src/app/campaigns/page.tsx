'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import DashboardLayout from '@/components/DashboardLayout'
import api from '@/lib/api'
import type { Campaign } from '@/types'
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  CubeIcon,
  PlayIcon,
  PauseIcon,
  DocumentDuplicateIcon,
  TrashIcon,
  EyeIcon
} from '@heroicons/react/24/outline'

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const fetchCampaigns = async () => {
    try {
      const response = await api.get('/api/campaigns')
      setCampaigns(response.data.campaigns || [])
    } catch (error) {
      console.error('Failed to fetch campaigns:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePublish = async (campaignId: string) => {
    try {
      await api.post(`/api/campaigns/${campaignId}/publish`)
      await fetchCampaigns() // Refresh campaigns
    } catch (error) {
      console.error('Failed to publish campaign:', error)
    }
  }

  const handleDuplicate = async (campaignId: string) => {
    const newTitle = prompt('Enter a title for the duplicated campaign:')
    if (!newTitle) return

    try {
      await api.post(`/api/campaigns/${campaignId}/duplicate`, { newTitle })
      await fetchCampaigns() // Refresh campaigns
    } catch (error) {
      console.error('Failed to duplicate campaign:', error)
    }
  }

  const handleDelete = async (campaignId: string) => {
    if (!confirm('Are you sure you want to delete this campaign?')) return

    try {
      await api.delete(`/api/campaigns/${campaignId}`)
      await fetchCampaigns() // Refresh campaigns
    } catch (error) {
      console.error('Failed to delete campaign:', error)
    }
  }

  const filteredCampaigns = campaigns.filter(campaign => {
    const matchesSearch = campaign.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (campaign.description && campaign.description.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesFilter = filterStatus === 'all' || campaign.status === filterStatus
    return matchesSearch && matchesFilter
  })

  const getStatusBadge = (status: string) => {
    const styles = {
      draft: 'bg-gray-100 text-gray-800',
      active: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-blue-100 text-blue-800'
    }
    return `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status as keyof typeof styles] || styles.draft}`
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="bg-white p-6 rounded-lg shadow">
                <div className="h-6 bg-gray-200 rounded mb-2"></div>
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
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Campaigns</h1>
            <p className="mt-2 text-gray-600">Manage your advertising campaigns across all platforms.</p>
          </div>
          <Link
            href="/campaigns/new"
            className="btn-primary"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            New Campaign
          </Link>
        </div>

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search campaigns..."
                  className="input pl-10"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <FunnelIcon className="h-5 w-5 text-gray-400" />
              <select
                className="input"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <option value="all">All Status</option>
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Campaigns List */}
        {filteredCampaigns.length > 0 ? (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {filteredCampaigns.map((campaign) => (
                <li key={campaign.id}>
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center">
                          <CubeIcon className="h-5 w-5 text-gray-400 mr-3" />
                          <div>
                            <h3 className="text-lg font-medium text-gray-900">{campaign.title}</h3>
                            {campaign.description && (
                              <p className="text-sm text-gray-500 mt-1">{campaign.description}</p>
                            )}
                          </div>
                        </div>
                        <div className="mt-2 flex items-center space-x-4">
                          <span className={getStatusBadge(campaign.status)}>
                            {campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
                          </span>
                          <span className="text-sm text-gray-500">
                            Budget: ${campaign.budget.toFixed(2)}
                          </span>
                          {campaign.platforms && campaign.platforms.length > 0 && (
                            <span className="text-sm text-gray-500">
                              {campaign.platforms.length} platform{campaign.platforms.length > 1 ? 's' : ''}
                            </span>
                          )}
                          <span className="text-sm text-gray-500">
                            Created: {new Date(campaign.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <Link
                          href={`/campaigns/${campaign.id}`}
                          className="p-2 text-gray-400 hover:text-gray-600"
                          title="View Details"
                        >
                          <EyeIcon className="h-5 w-5" />
                        </Link>
                        {campaign.status === 'draft' && (
                          <button
                            onClick={() => handlePublish(campaign.id)}
                            className="p-2 text-green-600 hover:text-green-800"
                            title="Publish Campaign"
                          >
                            <PlayIcon className="h-5 w-5" />
                          </button>
                        )}
                        {campaign.status === 'active' && (
                          <button
                            className="p-2 text-yellow-600 hover:text-yellow-800"
                            title="Pause Campaign"
                          >
                            <PauseIcon className="h-5 w-5" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDuplicate(campaign.id)}
                          className="p-2 text-blue-600 hover:text-blue-800"
                          title="Duplicate Campaign"
                        >
                          <DocumentDuplicateIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleDelete(campaign.id)}
                          className="p-2 text-red-600 hover:text-red-800"
                          title="Delete Campaign"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="bg-white p-12 rounded-lg shadow text-center">
            <CubeIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No campaigns found</h3>
            <p className="text-gray-500 mb-4">
              {searchTerm || filterStatus !== 'all' 
                ? 'Try adjusting your search or filters.'
                : 'Get started by creating your first campaign.'
              }
            </p>
            {!searchTerm && filterStatus === 'all' && (
              <Link href="/campaigns/new" className="btn-primary">
                <PlusIcon className="h-5 w-5 mr-2" />
                Create Campaign
              </Link>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
