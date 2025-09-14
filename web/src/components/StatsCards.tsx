interface Stat {
  label: string
  value: number
}

export default function StatsCards({ stats }: { stats: Stat[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {stats.map(s => (
        <div key={s.label} className="p-4 bg-white shadow">
          <div className="text-sm text-gray-500">{s.label}</div>
          <div className="text-2xl font-bold">{s.value}</div>
        </div>
      ))}
    </div>
  )
}
