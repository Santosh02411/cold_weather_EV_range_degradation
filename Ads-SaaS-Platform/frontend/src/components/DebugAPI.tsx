'use client'

import { useState, useEffect } from 'react'

export default function DebugAPI() {
  const [apiUrl, setApiUrl] = useState('')
  const [testResult, setTestResult] = useState('')
  const [loginResult, setLoginResult] = useState('')

  useEffect(() => {
    // Check if environment variable is loaded
    const url = process.env.NEXT_PUBLIC_API_URL
    setApiUrl(url || 'Not found')
  }, [])

  
  return (
    <div className="p-4 bg-gray-100 rounded-lg mb-4">
      <h3 className="text-lg font-bold mb-2">API Debug</h3>
      <p><strong>API URL:</strong> {apiUrl}</p>
    </div>
  )
}
