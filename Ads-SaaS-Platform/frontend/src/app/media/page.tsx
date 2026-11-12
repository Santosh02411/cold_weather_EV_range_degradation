'use client'

import { useState, useEffect } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import type { Media } from '@/types'
import {
  PhotoIcon,
  PlusIcon,
  TrashIcon,
  EyeIcon,
  ArrowUpTrayIcon
} from '@heroicons/react/24/outline'

export default function MediaPage() {
  const [media, setMedia] = useState<Media[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  useEffect(() => {
    fetchMedia()
  }, [])

  const fetchMedia = async () => {
    try {
      const response = await api.get('/api/media')
      setMedia(response.data.media || [])
    } catch (error) {
      console.error('Failed to fetch media:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a file to upload')
      return
    }

    setUploading(true)

    try {
      // For demo purposes, we'll just call the API without actual file upload
      // In production, you'd use FormData for file uploads
      const response = await api.post('/api/media/upload', {
        filename: selectedFile.name,
        mime_type: selectedFile.type,
        size: selectedFile.size
      })

      const newMedia = response.data.media
      setMedia(prev => [newMedia, ...prev])
      setSelectedFile(null)
      
      // Reset file input
      const fileInput = document.getElementById('file-upload') as HTMLInputElement
      if (fileInput) fileInput.value = ''
      
      toast.success('Media uploaded successfully!')
    } catch (error: any) {
      console.error('Failed to upload media:', error)
      toast.error(error.response?.data?.error || 'Failed to upload media')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (mediaId: string) => {
    if (!confirm('Are you sure you want to delete this media file?')) return

    try {
      await api.delete(`/api/media/${mediaId}`)
      setMedia(prev => prev.filter(m => m.id !== mediaId))
      toast.success('Media deleted successfully!')
    } catch (error: any) {
      console.error('Failed to delete media:', error)
      toast.error(error.response?.data?.error || 'Failed to delete media')
    }
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Media Library</h1>
          <p className="mt-2 text-gray-600">Manage your images, videos, and other media assets for campaigns.</p>
        </div>

        {/* Upload Section */}
        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Media</h2>
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            
            <div className="space-y-4">
              <div>
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="btn-primary inline-flex items-center">
                    <PlusIcon className="h-5 w-5 mr-2" />
                    Select File
                  </span>
                  <input
                    id="file-upload"
                    type="file"
                    className="hidden"
                    accept="image/*,video/*"
                    onChange={handleFileSelect}
                  />
                </label>
              </div>
              
              {selectedFile && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">
                    Selected: <span className="font-medium">{selectedFile.name}</span>
                  </p>
                  <p className="text-xs text-gray-500">
                    Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              )}
              
              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Uploading...' : 'Upload Media'}
              </button>
            </div>
          </div>
        </div>

        {/* Media Grid */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Media Files</h2>
          
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading media...</p>
            </div>
          ) : media.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {media.map((item) => (
                <div key={item.id} className="border rounded-lg overflow-hidden">
                  <div className="aspect-w-16 aspect-h-9 bg-gray-100">
                    <img
                      src={item.url}
                      alt={item.original_name}
                      className="w-full h-48 object-cover"
                    />
                  </div>
                  
                  <div className="p-4">
                    <h3 className="font-medium text-gray-900 truncate">{item.original_name}</h3>
                    <p className="text-sm text-gray-500">
                      {(item.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    
                    <div className="mt-4 flex items-center justify-between">
                      <button
                        className="p-2 text-gray-600 hover:text-gray-900"
                        title="View"
                      >
                        <EyeIcon className="h-5 w-5" />
                      </button>
                      
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="p-2 text-red-600 hover:text-red-800"
                        title="Delete"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <PhotoIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500 mb-4">No media files found.</p>
              <p className="text-sm text-gray-400">Upload your first media file to get started.</p>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
