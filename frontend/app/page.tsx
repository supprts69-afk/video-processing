'use client'

import { useEffect, useState, useRef } from 'react'
import { supabase } from '@/lib/supabaseClient'
import Hls from 'hls.js'

// কাস্টম HLS Video Player Component
const HLSPlayer = ({ url }: { url: string }) => {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    if (Hls.isSupported()) {
      const hls = new Hls()
      hls.loadSource(url)
      hls.attachMedia(video)
      return () => hls.destroy()
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = url
    }
  }, [url])

  return <video ref={videoRef} controls autoPlay className="w-full rounded-lg shadow-lg bg-black" />
}

export default function Dashboard() {
  const [jobs, setJobs] = useState<any[]>([])
  const [workers, setWorkers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [videoUrl, setVideoUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [playingJobId, setPlayingJobId] = useState<string | null>(null)

  const fetchData = async () => {
    const { data: jobsData } = await supabase.from('jobs').select('*').order('created_at', { ascending: false }).limit(10)
    if (jobsData) setJobs(jobsData)

    const { data: workersData } = await supabase.from('workers').select('*').order('last_heartbeat_at', { ascending: false })
    if (workersData) setWorkers(workersData)
    
    setLoading(false)
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!videoUrl) return
    setSubmitting(true)
    
    try {
      const res = await fetch('/api/v1/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_url: videoUrl })
      })
      if (res.ok) {
        setVideoUrl('')
        fetchData()
      }
    } catch (err) {
      console.error(err)
    }
    setSubmitting(false)
  }

  if (loading) return <div className="flex items-center justify-center min-h-screen">Loading dashboard...</div>

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8 bg-gray-50 min-h-screen">
      <header className="border-b pb-6 mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900">Distributed HLS Video Platform</h1>
      </header>

      <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Process New Video</h2>
        <form onSubmit={handleCreateJob} className="flex gap-4">
          <input
            type="url" required placeholder="Enter YouTube or Drive link..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
            value={videoUrl} onChange={(e) => setVideoUrl(e.target.value)}
          />
          <button type="submit" disabled={submitting} className="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg">
            {submitting ? 'Submitting...' : 'Process Video'}
          </button>
        </form>
      </section>

      {/* Video Player Modal */}
      {playingJobId && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-4 rounded-xl w-full max-w-4xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg">Seamless Playback (HLS)</h3>
              <button onClick={() => setPlayingJobId(null)} className="text-red-600 font-bold">Close</button>
            </div>
            {/* Playlist Endpoint-এ রিকোয়েস্ট পাঠানো হচ্ছে */}
            <HLSPlayer url={`/api/v1/jobs/${playingJobId}/playlist.m3u8`} />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <section className="lg:col-span-1">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Active Servers</h2>
          <div className="space-y-3">
            {workers.map(w => (
              <div key={w.id} className="p-4 bg-white rounded-xl shadow-sm border">
                <span className="font-semibold">{w.name}</span>
                <span className={`block mt-2 text-xs font-bold ${w.status === 'busy' ? 'text-amber-600' : 'text-emerald-600'}`}>
                  {w.status.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </section>

        <section className="lg:col-span-2">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Processing Jobs</h2>
          <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-gray-100 text-gray-600">
                <tr><th className="p-4">Job ID</th><th className="p-4">Status</th><th className="p-4">Progress</th><th className="p-4">Action</th></tr>
              </thead>
              <tbody className="divide-y">
                {jobs.map(job => (
                  <tr key={job.id}>
                    <td className="p-4 font-mono text-sm">{job.id.substring(0,8)}...</td>
                    <td className="p-4 font-bold text-sm uppercase">{job.status}</td>
                    <td className="p-4">{job.completed_task_count} / {job.expected_task_count || '?'} Parts</td>
                    <td className="p-4">
                      {job.status === 'completed' ? (
                        <button onClick={() => setPlayingJobId(job.id)} className="text-white bg-green-600 px-3 py-1 rounded text-sm font-bold">
                          ▶ Play Video
                        </button>
                      ) : <span className="text-gray-400 text-sm">Processing...</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  )
}
