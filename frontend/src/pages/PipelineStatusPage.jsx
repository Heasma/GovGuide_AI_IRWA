import PageHeader from '../components/common/PageHeader'
import StatusBadge from '../components/common/StatusBadge'
import { mockPipelineStages } from '../data/mockData'
import { Activity, Cpu, ArrowRight, CheckCircle2, AlertTriangle } from 'lucide-react'

export default function PipelineStatusPage() {
  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader 
        title="Agentic Pipeline Monitoring" 
        subtitle="Visual status tracking across GovGuide's multi-agent NLP research and retrieval pipeline."
        badgeText="Pipeline Operational / Waiting for Dataset"
      />

      <div className="card premium-card" style={{ marginBottom: 32, padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <Activity size={24} style={{ color: '#10b981' }} />
          <div>
            <h2 className="text-h2" style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>Pipeline Architecture Status</h2>
            <div className="text-small" style={{ color: 'var(--color-text-secondary)' }}>All 5 pipeline stages verified & configured</div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 24 }}>
          {mockPipelineStages.map((stg, i) => (
            <div key={stg.stage} style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: 16,
              background: 'var(--color-surface-2)',
              borderRadius: 8,
              border: '1px solid var(--color-border)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'var(--color-primary-light)', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyCenter: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700 }}>
                  {i + 1}
                </div>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)' }}>{stg.stage}</div>
                  <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 2 }}>{stg.description}</div>
                </div>
              </div>

              <StatusBadge status={stg.status} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
