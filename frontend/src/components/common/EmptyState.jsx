import { Database, AlertCircle } from 'lucide-react'

export default function EmptyState({ icon: Icon = Database, title, message, badgeText = "Integration Pending" }) {
  return (
    <div className="card premium-card" style={{ padding: '48px 24px', textAlign: 'center', maxWidth: 640, margin: '24px auto' }}>
      <div style={{
        width: 64,
        height: 64,
        borderRadius: '50%',
        background: 'rgba(99, 102, 241, 0.1)',
        color: 'var(--color-accent)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto 16px'
      }}>
        <Icon size={28} />
      </div>
      <div className="pending-badge" style={{ marginBottom: 12, display: 'inline-flex', alignItems: 'center' }}>
        <AlertCircle size={12} style={{ marginRight: 4 }} /> {badgeText}
      </div>
      <h3 className="text-h2" style={{ marginBottom: 8, fontSize: 18, fontWeight: 700 }}>{title}</h3>
      <p className="text-body" style={{ color: 'var(--color-text-secondary)', maxWidth: 460, margin: '0 auto', lineHeight: 1.6 }}>
        {message}
      </p>
    </div>
  )
}
