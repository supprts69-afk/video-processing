// frontend/app/jobs/new/page.tsx
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function NewJob() {
  const [sourceUrl, setSourceUrl] = useState('')
  const [segmentDuration, setSegmentDuration] = useState(30)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const res = await fetch(`${process.env.NEXT_PUBLIC_MOTHER_API_URL}/api/v1/jobs`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.NEXT_PUBLIC_ADMIN_TOKEN}` // Handled via secure proxy in prod
      },
      body: JSON.stringify({
        source_url: sourceUrl,
        processing_profile: { segment_duration: segmentDuration }
      })
    })

    if (res.ok) {
      router.push('/')
      router.refresh()
    } else {
      alert("Failed to submit job")
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Create New Processing Job</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Source Video URL (Cloudinary or Public MP4)</label>
          <input 
            type="url" 
            required
            className="w-full border p-2 rounded"
            value={sourceUrl}
            onChange={e => setSourceUrl(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Segment Duration (Seconds)</label>
          <input 
            type="number" 
            min="10" max="300"
            className="w-full border p-2 rounded"
            value={segmentDuration}
            onChange={e => setSegmentDuration(Number(e.target.value))}
          />
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">
          Submit Job
        </button>
      </form>
    </div>
  )
}
