import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'
import DataTable from '../components/DataTable'
import FiltersBar from '../components/FiltersBar'

export default function Interfaces() {
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [page, setPage] = useState(1)
  const pageSize = 10

  const { data } = useQuery({
    queryKey: ['interfaces', filters, page],
    queryFn: () =>
      api
        .get('/provisioning/interfaces', {
          params: { page, page_size: pageSize, sort_by: 'pri_id', sort_dir: 'asc', ...filters },
        })
        .then(r => r.data),
  })

  const columns = [
    { header: 'ID', accessorKey: 'pri_id' },
    { header: 'MSISDN', accessorKey: 'pri_cellular_number' },
    { header: 'Status', accessorKey: 'pri_status' },
  ]

  return (
    <div>
      <h1 className="text-xl mb-4">Interfaces</h1>
      <FiltersBar onChange={f => { setFilters(f); setPage(1) }} />
      <DataTable columns={columns} data={data?.rows || []} />
      <div className="mt-2 space-x-2">
        <button disabled={page === 1} onClick={() => setPage(p => p - 1)} className="px-2 border">
          Prev
        </button>
        <button
          disabled={(data?.rows.length || 0) < pageSize}
          onClick={() => setPage(p => p + 1)}
          className="px-2 border"
        >
          Next
        </button>
      </div>
    </div>
  )
}
