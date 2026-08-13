import PageHeader from '../components/common/PageHeader'
import StatCard from '../components/common/StatCard'
import StatusBadge from '../components/common/StatusBadge'
import { mockKnowledgeSources } from '../data/mockData'
import { ShieldCheck, Database, CheckCircle, Clock, ExternalLink } from 'lucide-react'

export default function VerifiedSourcesPage() {
  const verifiedCount = mockKnowledgeSources.filter(s => s.verificationStatus === 'Verified').length
  const pendingCount = mockKnowledgeSources.filter(s => s.verificationStatus.includes('Pending')).length

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader 
        title="Verified Sources Dashboard" 
        subtitle="Source authenticity verification and domain trustworthiness evaluation."
      />

      <div className="stat-grid" style={{ marginBottom: 32, gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <StatCard title="Total Sources" value={mockKnowledgeSources.length} icon={Database} color="blue" />
        <StatCard title="Verified" value={verifiedCount} icon={CheckCircle} color="green" />
        <StatCard title="Pending Review" value={pendingCount} icon={Clock} color="amber" />
        <StatCard title="Overall Reliability" value="98.2%" icon={ShieldCheck} color="indigo" />
      </div>

      <div className="card premium-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', fontWeight: 700, fontSize: 16 }}>
          Source Verification Ledger
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: 'var(--color-surface-2)', borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Source</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Type</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Last Checked</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Score</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {mockKnowledgeSources.map(src => (
                <tr key={src.id} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 600 }}>{src.name}</td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)' }}>{src.type}</td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-text-muted)' }}>{src.lastUpdated}</td>
                  <td style={{ padding: '14px 16px' }}><StatusBadge status={src.verificationStatus} /></td>
                  <td style={{ padding: '14px 16px', fontWeight: 700, color: 'var(--color-success)' }}>{src.reliabilityScore}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <a href={src.url} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      Verify <ExternalLink size={12} />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
