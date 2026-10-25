'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabaseClient'

export default function Dashboard() {
  const [jobs, setJobs] = useState<any[]>([])
  const [workers, setWorkers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [videoUrl, setVideoUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // ডেটা ফেচ করার ফাংশন
  const fetchData = async () => {
    const { data: jobsData } = await supabase
      .from('jobs')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(10)
    if (jobsData) setJobs(jobsData)

    const { data: workersData } = await supabase
      .from('workers')
      .select('*')
      .order('last_heartbeat_at', { ascending: false })
    if (workersData) setWorkers(workersData)
    
    setLoading(false)
  }

  // প্রতি ৫ সেকেন্ড পর পর অটোমেটিক ডেটা রিফ্রেশ
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  // নতুন জব সাবমিট করার ফাংশন
  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!videoUrl) return
    setSubmitting(true)
    
    try {
      const res = await fetch('/api/v1/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_url: videoUrl,
          processing_profile: { segment_duration: 15, resolution: "1920x1080", codec: "libx264", preset: "fast" }
        })
      })
      
      if (res.ok) {
        setVideoUrl('')
        fetchData() // সাথে সাথে লিস্ট আপডেট করা
      } else {
        alert("Failed to create job")
      }
    } catch (err) {
      console.error(err)
    }
    setSubmitting(false)
  }

  if (loading) return <div className="flex items-center justify-center min-h-screen text-lg font-medium text-gray-600">Loading dashboard...</div>

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      <header className="border-b pb-6 mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">Distributed Video Platform</h1>
        <p className="text-gray-500 mt-2">Manage FFmpeg workers and video processing jobs</p>
      </header>

      {/* Job Submission Form */}
      <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Create New Job</h2>
        <form onSubmit={handleCreateJob} className="flex gap-4">
          <input
            type="url"
            required
            placeholder="Enter public .mp4 video URL (e.g., https://example.com/video.mp4)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
          />
          <button 
            type="submit" 
            disabled={submitting}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg disabled:opacity-50 transition-colors"
          >
            {submitting ? 'Submitting...' : 'Process Video'}
          </button>
        </form>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Workers List */}
        <section className="lg:col-span-1">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center justify-between">
            Active Workers
            <span className="bg-blue-100 text-blue-800 text-xs px-2.5 py-0.5 rounded-full">{workers.length}</span>
          </h2>
          <div className="space-y-3">
            {workers.length === 0 && <p className="text-gray-500 text-sm">No workers registered yet.</p>}
            {workers.map(w => (
              <div key={w.id} className="p-4 bg-white rounded-xl shadow-sm border border-gray-100 flex justify-between items-center">
                <div className="flex flex-col">
                  <span className="font-semibold text-gray-700">{w.name}</span>
                  <span className="text-xs text-gray-400 font-mono mt-1">{w.id.substring(0,8)}</span>
                </div>
                <span className={`px-3 py-1 text-xs font-bold uppercase rounded-full tracking-wider ${w.status === 'busy' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                  {w.status}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Jobs List */}
        <section className="lg:col-span-2">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Recent Processing Jobs</h2>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100 text-gray-500 text-sm uppercase tracking-wider">
                  <th className="p-4 font-medium">Job ID</th>
                  <th className="p-4 font-medium">Status</th>
                  <th className="p-4 font-medium">Progress</th>
                  <th className="p-4 font-medium">Link</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {jobs.length === 0 && (
                  <tr><td colSpan={4} className="p-8 text-center text-gray-500">No jobs found.</td></tr>
                )}
                {jobs.map(job => (
                  <tr key={job.id} className="hover:bg-gray-50 transition-colors">
                    <td className="p-4 font-mono text-sm text-gray-600">{job.id.substring(0,8)}...</td>
                    <td className="p-4">
                      <span className={`px-2.5 py-1 text-xs font-semibold uppercase rounded-full tracking-wide 
                        ${job.status === 'completed' ? 'bg-green-100 text-green-700' : 
                          job.status === 'queued' ? 'bg-gray-100 text-gray-700' : 'bg-blue-100 text-blue-700'}`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="p-4 text-sm font-medium text-gray-700">
                      {job.completed_task_count} / {job.expected_task_count} Tasks
                    </td>
                    <td className="p-4">
                      {job.output_url ? (
                        <a href={job.output_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-sm font-medium">View</a>
                      ) : (
                        <span className="text-gray-400 text-sm">-</span>
                      )}
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
