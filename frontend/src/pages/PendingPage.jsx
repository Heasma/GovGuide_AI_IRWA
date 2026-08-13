import { AlertCircle } from 'lucide-react'

export default function PendingPage({ title, message }) {
  return (
    <div style={{ padding: '32px 24px', maxWidth: 800, margin: '0 auto' }} className="fade-in">
      <div className="dashboard-header" style={{ marginBottom: 32 }}>
        <h1 className="text-display" style={{ marginBottom: 12 }}>{title}</h1>
        
        <div className="card premium-card" style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
          <div style={{ color: 'var(--color-accent)' }}>
            <AlertCircle size={24} />
          </div>
          <div>
            <h3 className="text-h3" style={{ marginBottom: 8, color: '#f59e0b' }}>Integration Pending</h3>
            <p className="text-body" style={{ color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
              {message}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
