import PageHeader from '../components/common/PageHeader'
import EmptyState from '../components/common/EmptyState'
import { DatabaseZap, AlertCircle, RefreshCw } from 'lucide-react'

export default function DatasetStatusPage() {
  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader 
        title="Dataset Integration Status" 
        subtitle="Real-time monitoring of government master registry data ingestion."
        badgeText="Dataset Pending"
      />

      <div className="card premium-card" style={{ marginBottom: 32, padding: 24, borderLeft: '4px solid #f59e0b' }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
          <div style={{ background: '#fffbeb', color: '#b45309', width: 44, height: 44, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <DatabaseZap size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h2 className="text-h2" style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>Dataset Status: Pending</h2>
              <span className="pending-badge" style={{ fontSize: 11, background: '#fffbeb', color: '#b45309', border: '1px solid #fde68a', padding: '2px 8px', borderRadius: 12 }}>
                Pending Integration
              </span>
            </div>
            <p className="text-body" style={{ color: 'var(--color-text-secondary)', lineHeight: 1.6, margin: 0 }}>
              The actual official government-services dataset has not yet been connected. All database tables and search structures operate on preliminary demonstration schemas. No official government service data has been fabricated or inserted.
            </p>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 20, marginBottom: 32 }}>
        <div className="card premium-card" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>Dataset Status</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#f59e0b' }}>Pending</div>
        </div>
        <div className="card premium-card" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>Records Loaded</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-muted)' }}>Not Available</div>
        </div>
        <div className="card premium-card" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>Last Sync Attempt</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-muted)' }}>Not Available</div>
        </div>
        <div className="card premium-card" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>Source Connection</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-muted)' }}>Not Connected</div>
        </div>
      </div>

      <EmptyState 
        icon={DatabaseZap}
        title="No dataset connected yet"
        message="When the official government services dataset export is delivered, the automated ingestion pipeline will process, chunk, vector-embed, and index all services."
        badgeText="Awaiting Dataset Export"
      />
    </div>
  )
}
