// frontend/app/page.tsx
import { supabase } from '@/lib/supabaseClient'

export default async function Dashboard() {
  const { data: jobs } = await supabase
    .from('jobs')
    .select('id, status, expected_task_count, completed_task_count')
    .order('created_at', { ascending: false })
    .limit(10)

  const { data: workers } = await supabase
    .from('workers')
    .select('id, name, status, last_heartbeat_at')

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold">Distributed Video Platform</h1>
      
      <section>
        <h2 className="text-xl font-semibold mb-4">Active Workers</h2>
        <div className="grid grid-cols-3 gap-4">
          {workers?.map(w => (
            <div key={w.id} className="p-4 border rounded shadow-sm">
              <div className="flex justify-between">
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
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b text-left">
              <th className="p-2">Job ID</th>
              <th className="p-2">Status</th>
              <th className="p-2">Progress</th>
            </tr>
          </thead>
          <tbody>
            {jobs?.map(job => (
              <tr key={job.id} className="border-b">
                <td className="p-2 font-mono text-sm">{job.id.substring(0,8)}...</td>
                <td className="p-2">{job.status}</td>
                <td className="p-2">
                  {job.completed_task_count} / {job.expected_task_count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
