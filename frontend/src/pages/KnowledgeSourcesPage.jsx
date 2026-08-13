import { useState } from 'react'
import PageHeader from '../components/common/PageHeader'
import SearchBar from '../components/common/SearchBar'
import StatusBadge from '../components/common/StatusBadge'
import { mockKnowledgeSources } from '../data/mockData'
import { Database, ExternalLink, RefreshCw } from 'lucide-react'

export default function KnowledgeSourcesPage() {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredSources = mockKnowledgeSources.filter(src => 
    src.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    src.type.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader 
        title="Knowledge Sources Management" 
        subtitle="Monitored government web portals, legislative gazette feeds, and official knowledge domains."
      />

      <div style={{ marginBottom: 24 }}>
        <SearchBar value={searchTerm} onChange={setSearchTerm} onClear={() => setSearchTerm('')} placeholder="Search knowledge sources..." />
      </div>

      <div className="card premium-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: 'var(--color-surface-2)', borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Source Name</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Source Type</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Indexed Docs</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Last Updated</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Reliability</th>
              </tr>
            </thead>
            <tbody>
              {filteredSources.map(src => (
                <tr key={src.id} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 600 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Database size={16} style={{ color: 'var(--color-accent)' }} />
                      <a href={src.url} target="_blank" rel="noreferrer" style={{ color: 'var(--color-text-primary)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        {src.name} <ExternalLink size={12} style={{ opacity: 0.6 }} />
                      </a>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)' }}>{src.type}</td>
                  <td style={{ padding: '14px 16px', fontWeight: 600 }}>{src.documentCount}</td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-text-muted)' }}>{src.lastUpdated}</td>
                  <td style={{ padding: '14px 16px' }}><StatusBadge status={src.verificationStatus} /></td>
                  <td style={{ padding: '14px 16px', fontWeight: 700, color: 'var(--color-success)' }}>{src.reliabilityScore}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
