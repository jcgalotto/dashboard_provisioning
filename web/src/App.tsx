import { Link, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Interfaces from './pages/Interfaces'
import Logs from './pages/Logs'

export default function App() {
  return (
    <div className="p-4">
      <nav className="mb-4 space-x-4">
        <Link to="/">Dashboard</Link>
        <Link to="/interfaces">Interfaces</Link>
        <Link to="/logs">Logs</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/interfaces" element={<Interfaces />} />
        <Route path="/logs" element={<Logs />} />
      </Routes>
    </div>
  )
}
