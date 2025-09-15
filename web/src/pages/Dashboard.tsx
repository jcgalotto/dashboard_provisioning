import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'
import StatsCards from '../components/StatsCards'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts'

export default function Dashboard() {
  const { data } = useQuery({
    queryKey: ['stats'],
    queryFn: () =>
      api
        .get('/provisioning/interfaces/stats', {
          params: { group_by: 'status', from: '2020-01-01', to: '2030-01-01' },
        })
        .then(r => r.data),
  })

  const stats = (data || []).map((s: { group_key: string; total: number }) => ({ label: s.group_key, value: s.total }))

  return (
    <div>
      <h1 className="text-xl mb-4">Dashboard</h1>
      <StatsCards stats={stats} />
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={stats}>
          <XAxis dataKey="label" />
          <YAxis />
          <Bar dataKey="value" fill="#3182ce" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
