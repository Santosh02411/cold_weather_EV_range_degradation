'use client'

import { useState, useEffect } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import api from '@/lib/api'
import type { StatusOverview, Job, Log } from '@/types'
import {
  ChartBarIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  ArrowPathIcon,
  FunnelIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline'

export default function StatusPage() {
  const [statusOverview, setStatusOverview] = useState<StatusOverview | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [logs, setLogs] = useState<Log[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'jobs' | 'logs'>('overview')
  const [jobFilter, setJobFilter] = useState('all')
  const [logFilter, setLogFilter] = useState('all')

  useEffect(() => {
    fetchStatusData()
  }, [])

  const fetchStatusData = async () => {
    try {
      const [overviewRes, jobsRes, logsRes] = await Promise.all([
        api.get('/api/status/overview'),
        api.get('/api/status/jobs'),
        api.get('/api/status/logs')
      ])
      
      setStatusOverview(overviewRes.data)
      setJobs(jobsRes.data.jobs || [])
      setLogs(logsRes.data.logs || [])
    } catch (error) {
      console.error('Failed to fetch status data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRetryJob = async (jobId: string) => {
    try {
      await api.post(`/api/status/jobs/${jobId}/retry`)
      fetchStatusData() // Refresh data
    } catch (error) {
      console.error('Failed to retry job:', error)
    }
  }

  const getStatusColor = (status: string) => {
    const colors = {
      success: 'text-green-600',
      failed: 'text-red-600',
      processing: 'text-blue-600',
      pending: 'text-yellow-600'
    }
    return colors[status as keyof typeof colors] || 'text-gray-600'
  }

  const getStatusBg = (status: string) => {
    const colors = {
      success: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      processing: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800'
    }
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  const getLogLevelIcon = (level: string) => {
    switch (level) {
      case 'error': return <ExclamationCircleIcon className="h-4 w-4 text-red-600" />
      case 'warn': return <ExclamationCircleIcon className="h-4 w-4 text-yellow-600" />
      case 'info': return <CheckCircleIcon className="h-4 w-4 text-blue-600" />
      default: return <ClockIcon className="h-4 w-4 text-gray-600" />
    }
  }

  const filteredJobs = jobs.filter(job => 
    jobFilter === 'all' || job.status === jobFilter
  )

  const filteredLogs = logs.filter(log => 
    logFilter === 'all' || log.level === logFilter
  )

  if (loading) {
    return (
      <DashboardLayout>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white p-6 rounded-lg shadow">
                <div className="h-8 bg-gray-200 rounded mb-2"></div>
                <div className="h-12 bg-gray-200 rounded"></div>
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
          <h1 className="text-3xl font-bold text-gray-900">Status & Monitoring</h1>
          <p className="mt-2 text-gray-600">Monitor your campaigns, jobs, and system activity.</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {['overview', 'jobs', 'logs'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && statusOverview && (
          <div className="space-y-8">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <ChartBarIcon className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Campaigns</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {statusOverview.campaigns.total_campaigns}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-3 bg-green-100 rounded-lg">
                    <CheckCircleIcon className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Active Campaigns</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {statusOverview.campaigns.active_campaigns}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-3 bg-yellow-100 rounded-lg">
                    <ClockIcon className="h-6 w-6 text-yellow-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Pending Jobs</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {statusOverview.jobs.pending_jobs}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-3 bg-purple-100 rounded-lg">
                    <ExclamationCircleIcon className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Failed Jobs</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {statusOverview.jobs.failed_jobs}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
              <div className="space-y-4">
                {statusOverview.recentActivity.slice(0, 10).map((log) => (
                  <div key={log.id} className="flex items-start space-x-3">
                    <div className="mt-1">
                      {getLogLevelIcon(log.level)}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-900">{log.message}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(log.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Jobs Tab */}
        {activeTab === 'jobs' && (
          <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center space-x-4">
                <FunnelIcon className="h-5 w-5 text-gray-400" />
                <select
                  className="input"
                  value={jobFilter}
                  onChange={(e) => setJobFilter(e.target.value)}
                >
                  <option value="all">All Jobs</option>
                  <option value="pending">Pending</option>
                  <option value="processing">Processing</option>
                  <option value="success">Success</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
            </div>

            {/* Jobs List */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {filteredJobs.map((job) => (
                  <li key={job.id}>
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBg(job.status)}`}>
                              {job.status}
                            </span>
                            <span className="ml-3 text-sm font-medium text-gray-900">
                              {job.action} - {job.campaign_title || 'Unknown Campaign'}
                            </span>
                          </div>
                          <div className="mt-2 text-sm text-gray-500">
                            Platform: {job.platform_name || 'Unknown'} • 
                            Created: {new Date(job.created_at).toLocaleString()}
                            {job.processed_at && ` • Processed: ${new Date(job.processed_at).toLocaleString()}`}
                          </div>
                          {job.error_message && (
                            <div className="mt-2 text-sm text-red-600">
                              Error: {job.error_message}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          {job.status === 'failed' && (
                            <button
                              onClick={() => handleRetryJob(job.id)}
                              className="p-2 text-blue-600 hover:text-blue-800"
                              title="Retry Job"
                            >
                              <ArrowPathIcon className="h-5 w-5" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Logs Tab */}
        {activeTab === 'logs' && (
          <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center space-x-4">
                <FunnelIcon className="h-5 w-5 text-gray-400" />
                <select
                  className="input"
                  value={logFilter}
                  onChange={(e) => setLogFilter(e.target.value)}
                >
                  <option value="all">All Logs</option>
                  <option value="error">Errors</option>
                  <option value="warn">Warnings</option>
                  <option value="info">Info</option>
                  <option value="debug">Debug</option>
                </select>
              </div>
            </div>

            {/* Logs List */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {filteredLogs.map((log) => (
                  <li key={log.id}>
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-start space-x-3">
                        <div className="mt-1">
                          {getLogLevelIcon(log.level)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBg(log.level)}`}>
                              {log.level.toUpperCase()}
                            </span>
                            <span className="ml-3 text-sm font-medium text-gray-900">
                              {log.message}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(log.created_at).toLocaleString()}
                            {log.campaign_id && ` • Campaign: ${log.campaign_id}`}
                            {log.platform_id && ` • Platform: ${log.platform_id}`}
                          </p>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
