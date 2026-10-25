// frontend/app/page.tsx
'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabaseClient'

export default function Dashboard() {
  const [jobs, setJobs] = useState<any[]>([])
  const [workers, setWorkers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      // Jobs ফেচ করা
      const { data: jobsData } = await supabase
        .from('jobs')
        .select('id, status, expected_task_count, completed_task_count')
        .order('created_at', { ascending: false })
        .limit(10)
      
      if (jobsData) setJobs(jobsData)

      // Workers ফেচ করা
      const { data: workersData } = await supabase
        .from('workers')
        .select('id, name, status, last_heartbeat_at')
      
      if (workersData) setWorkers(workersData)
      setLoading(false)
    }

    fetchData()
  }, [])

  if (loading) return <div className="p-8">Loading dashboard...</div>

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold">Distributed Video Platform</h1>
      
      <section>
        <h2 className="text-xl font-semibold mb-4">Active Workers</h2>
        <div className="grid grid-cols-3 gap-4">
          {workers.length === 0 && <p className="text-gray-500">No workers registered yet.</p>}
          {workers.map(w => (
            <div key={w.id} className="p-4 border rounded shadow-sm">
              <div className="flex justify-between items-center">
                <span className="font-mono text-sm">{w.name}</span>
                <span className={`px-2 py-1 text-xs rounded ${w.status === 'busy' ? 'bg-green-100' : 'bg-gray-100'}`}>
                  {w.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4">Recent Jobs</h2>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b text-left bg-gray-50">
                <th className="p-3">Job ID</th>
                <th className="p-3">Status</th>
                <th className="p-3">Progress</th>
              </tr>
            </thead>
            <tbody>
              {jobs.length === 0 && (
                <tr><td colSpan={3} className="p-3 text-gray-500">No jobs found.</td></tr>
              )}
              {jobs.map(job => (
                <tr key={job.id} className="border-b">
                  <td className="p-3 font-mono text-sm">{job.id.substring(0,8)}...</td>
                  <td className="p-3">
                    <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-sm uppercase">
                      {job.status}
                    </span>
                  </td>
                  <td className="p-3">
                    {job.completed_task_count} / {job.expected_task_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
