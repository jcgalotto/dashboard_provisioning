import { useState } from 'react'

interface Props {
  onChange: (filters: Record<string, string>) => void
}

export default function FiltersBar({ onChange }: Props) {
  const [msisdn, setMsisdn] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [neService, setNeService] = useState('')

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <input className="border p-2" value={msisdn} onChange={e => setMsisdn(e.target.value)} placeholder="MSISDN" />
      <input className="border p-2" value={status} onChange={e => setStatus(e.target.value)} placeholder="Status" />
      <input className="border p-2" value={error} onChange={e => setError(e.target.value)} placeholder="Error" />
      <input className="border p-2" value={neService} onChange={e => setNeService(e.target.value)} placeholder="NE Service" />
      <button
        onClick={() => onChange({ msisdn, status, error_code: error, ne_service: neService })}
        className="bg-blue-600 text-white px-4"
      >
        Buscar
      </button>
    </div>
  )
}
