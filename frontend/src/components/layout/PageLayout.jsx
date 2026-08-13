import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function PageLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <div className="page-container">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
