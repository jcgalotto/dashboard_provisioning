import { useState } from 'react'
import api from '../lib/api'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const submit = async () => {
    const { data } = await api.post('/auth/login', { username, password })
    localStorage.setItem('token', data.access_token)
    window.location.href = '/'
  }

  return (
    <div className="p-4 max-w-sm mx-auto space-y-2">
      <input
        className="border p-2 w-full"
        placeholder="Usuario"
        value={username}
        onChange={e => setUsername(e.target.value)}
      />
      <input
        className="border p-2 w-full"
        placeholder="Clave"
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
      />
      <button className="bg-blue-600 text-white px-4" onClick={submit}>
        Login
      </button>
    </div>
  )
}
