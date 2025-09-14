import { useEffect, useState } from 'react'

export default function Logs() {
  const [lines, setLines] = useState<string[]>([])
  useEffect(() => {
    const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/api/logs/stream')
    ws.onmessage = e => setLines(l => [...l.slice(-100), e.data])
    return () => ws.close()
  }, [])
  return (
    <div>
      <h1 className="text-xl mb-4">Logs</h1>
      <pre className="bg-black text-green-400 p-2 h-96 overflow-auto">
        {lines.map((l, i) => (
          <div key={i}>{l}</div>
        ))}
      </pre>
    </div>
  )
}
