'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import DashboardLayout from '@/components/DashboardLayout'
import api from '@/lib/api'
import type { StatusOverview } from '@/types'
import {
  ChartBarIcon,
  CubeIcon,
  CurrencyDollarIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  PlusIcon,
  ArrowTrendingUpIcon,
  PhotoIcon
} from '@heroicons/react/24/outline'

export default function DashboardPage() {
  const [statusOverview, setStatusOverview] = useState<StatusOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    fetchStatusOverview()
  }, [])

  const fetchStatusOverview = async () => {
    try {
      const response = await api.get('/api/status/overview')
      setStatusOverview(response.data)
    } catch (error) {
      console.error('Failed to fetch status overview:', error)
    } finally {
      setLoading(false)
    }
  }

  const stats = [
    {
      name: 'Total Campaigns',
      value: statusOverview?.campaigns.total_campaigns || 0,
      icon: CubeIcon,
      color: 'bg-blue-500',
      change: '+2 from last month',
      changeType: 'positive'
    },
    {
      name: 'Active Campaigns',
      value: statusOverview?.campaigns.active_campaigns || 0,
      icon: CheckCircleIcon,
      color: 'bg-green-500',
      change: '+1 from last week',
      changeType: 'positive'
    },
    {
      name: 'Total Budget',
      value: `$${(statusOverview?.campaigns.total_budget || 0).toFixed(2)}`,
      icon: CurrencyDollarIcon,
      color: 'bg-yellow-500',
      change: '+$500 from last month',
      changeType: 'positive'
    },
    {
      name: 'Connected Platforms',
      value: statusOverview?.platforms.connected_platforms || 0,
      icon: ChartBarIcon,
      color: 'bg-purple-500',
      change: 'No change',
      changeType: 'neutral'
    }
  ]

  const recentActivity = statusOverview?.recentActivity || []

  if (loading) {
    return (
      <DashboardLayout>
        <div className="animate-pulse">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white p-6 rounded-lg shadow">
                <div className="h-8 bg-gray-200 rounded mb-4"></div>
                <div className="h-12 bg-gray-200 rounded"></div>
              </div>
            ))}
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="h-8 bg-gray-200 rounded mb-4"></div>
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 rounded"></div>
              ))}
            </div>
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
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-gray-600">Welcome back! Here's an overview of your ad campaigns.</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => {
            const Icon = stat.icon
            return (
              <div key={stat.name} className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className={`${stat.color} p-3 rounded-lg`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                    <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                  </div>
                </div>
                <div className="mt-4">
                  <span className={`text-sm ${
                    stat.changeType === 'positive' ? 'text-green-600' : 
                    stat.changeType === 'negative' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {stat.change}
                  </span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Quick Actions */}
        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/campaigns/new"
              className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
            >
              <PlusIcon className="h-6 w-6 text-primary-600 mr-2" />
              <span className="text-primary-600 font-medium">Create Campaign</span>
            </Link>
            <Link
              href="/integrations"
              className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
            >
              <CubeIcon className="h-6 w-6 text-primary-600 mr-2" />
              <span className="text-primary-600 font-medium">Connect Platform</span>
            </Link>
            <Link
              href="/media"
              className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
            >
              <PhotoIcon className="h-6 w-6 text-primary-600 mr-2" />
              <span className="text-primary-600 font-medium">Upload Media</span>
            </Link>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
            <button className="text-primary-600 hover:text-primary-700 text-sm font-medium">
              View all
            </button>
          </div>
          
          {recentActivity.length > 0 ? (
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-start space-x-3">
                  <div className={`p-2 rounded-full ${
                    activity.level === 'error' ? 'bg-red-100' :
                    activity.level === 'warn' ? 'bg-yellow-100' :
                    activity.level === 'info' ? 'bg-blue-100' :
                    'bg-gray-100'
                  }`}>
                    {activity.level === 'error' && <ExclamationCircleIcon className="h-4 w-4 text-red-600" />}
                    {activity.level === 'warn' && <ExclamationCircleIcon className="h-4 w-4 text-yellow-600" />}
                    {activity.level === 'info' && <CheckCircleIcon className="h-4 w-4 text-blue-600" />}
                    {activity.level === 'debug' && <ClockIcon className="h-4 w-4 text-gray-600" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{activity.message}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(activity.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <ClockIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No recent activity</p>
            </div>
          )}
        </div>

        {/* Job Status */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Status</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Pending</span>
                <span className="text-sm font-medium text-gray-900">
                  {statusOverview?.jobs.pending_jobs || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Processing</span>
                <span className="text-sm font-medium text-blue-600">
                  {statusOverview?.jobs.processing_jobs || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Success</span>
                <span className="text-sm font-medium text-green-600">
                  {statusOverview?.jobs.success_jobs || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Failed</span>
                <span className="text-sm font-medium text-red-600">
                  {statusOverview?.jobs.failed_jobs || 0}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Platform Status</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Platforms</span>
                <span className="text-sm font-medium text-gray-900">
                  {statusOverview?.platforms.total_platforms || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Connected</span>
                <span className="text-sm font-medium text-green-600">
                  {statusOverview?.platforms.connected_platforms || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Disconnected</span>
                <span className="text-sm font-medium text-red-600">
                  {statusOverview?.platforms.disconnected_platforms || 0}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
