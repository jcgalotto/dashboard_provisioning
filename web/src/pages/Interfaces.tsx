import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'
import DataTable from '../components/DataTable'
import FiltersBar from '../components/FiltersBar'

interface Row {
  pri_id: number
  pri_cellular_number: string
  pri_status: string
}

export default function Interfaces() {
  const [filters, setFilters] = useState<Record<string, string>>({})
  const { data } = useQuery({
    queryKey: ['interfaces', filters],
    queryFn: () => api.get('/provisioning/interfaces', { params: { ...filters } }).then(r => r.data.data)
  })

  const columns = [
    { header: 'ID', accessorKey: 'pri_id' },
    { header: 'MSISDN', accessorKey: 'pri_cellular_number' },
    { header: 'Status', accessorKey: 'pri_status' }
  ]

  return (
    <div>
      <h1 className="text-xl mb-4">Interfaces</h1>
      <FiltersBar onChange={setFilters} />
      <DataTable columns={columns} data={data || []} />
    </div>
  )
}
