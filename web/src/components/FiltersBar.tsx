import { useState } from 'react'

interface Props {
  onChange: (filters: Record<string, string>) => void
}

export default function FiltersBar({ onChange }: Props) {
  const [msisdn, setMsisdn] = useState('')

  return (
    <div className="flex space-x-2 mb-4">
      <input
        value={msisdn}
        onChange={e => setMsisdn(e.target.value)}
        placeholder="MSISDN"
        className="border p-2"
      />
      <button
        onClick={() => onChange({ msisdn })}
        className="bg-blue-600 text-white px-4"
      >
        Buscar
      </button>
    </div>
  )
}
