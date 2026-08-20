/**
 * GovGuide AI — Knowledge Sources Management Page
 *
 * Backed by GET /api/v1/sources (real database records).
 * Displays an honest empty state when official_sources contains 0 records.
 * Zero fake sources, zero invented reliability scores.
 */

import { useState, useEffect, useCallback } from 'react'
import PageHeader from '../components/common/PageHeader'
import SearchBar from '../components/common/SearchBar'
import { governmentService } from '../services/governmentService'
import {
  Database,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  Loader2,
  ShieldCheck,
  Globe,
} from 'lucide-react'

export default function KnowledgeSourcesPage() {
  const [sources, setSources] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  const fetchSources = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await governmentService.listSources(0, 50)
      setSources(data?.items || [])
      setTotal(data?.total || 0)
    } catch (err) {
      const status = err?.response?.status
      if (status >= 500) setError('A server error occurred while loading knowledge sources.')
      else if (!err.response) setError('Unable to connect to the server. Please check your network.')
      else setError('Failed to retrieve knowledge sources from the database.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSources()
  }, [fetchSources])

  const filteredSources = sources.filter((src) =>
    (src.title && src.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (src.source_type && src.source_type.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (src.url && src.url.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader
        title="Knowledge Sources Registry"
        subtitle="Monitored official government repositories and public legislative domains configured in the RAG pipeline."
      />

      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <SearchBar
            value={searchTerm}
            onChange={setSearchTerm}
            onClear={() => setSearchTerm('')}
            placeholder="Search indexed knowledge sources..."
          />
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={fetchSources}
          title="Refresh sources"
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, height: 40 }}
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--color-text-muted)' }}>
          <Loader2 size={28} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 12px', display: 'block' }} />
          <p style={{ fontSize: 14 }}>Querying official sources repository...</p>
        </div>
      )}

      {!loading && error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, fontSize: 13, color: '#991b1b', marginBottom: 24 }}>
          <AlertCircle size={15} style={{ flexShrink: 0 }} /> {error}
        </div>
      )}

      {!loading && !error && filteredSources.length === 0 && (
        <div style={{ textAlign: 'center', padding: '64px 24px', color: 'var(--color-text-muted)' }}>
          <Database size={48} style={{ margin: '0 auto 16px', display: 'block', opacity: 0.25 }} />
          <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
            No knowledge sources are currently indexed.
          </h3>
          <p style={{ fontSize: 14, maxWidth: 520, margin: '0 auto 20px', lineHeight: 1.6 }}>
            The <strong>official_sources</strong> database table has not yet been populated with external crawled documents.
            Source documentation and legal gazette records will automatically appear here once indexed by the ingestion engine.
          </p>
          <div style={{ display: 'inline-block', padding: '8px 14px', background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: 6, fontSize: 12, color: 'var(--color-text-muted)' }}>
            Database Table: <code>official_sources</code> (0 records)
          </div>
        </div>
      )}

      {!loading && !error && filteredSources.length > 0 && (
        <div className="card premium-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'var(--color-surface-2)', borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Source Name / Title</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Source Type</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Verified Timestamp</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Indexed Date</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredSources.map((src) => (
                  <tr key={src.id} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                    <td style={{ padding: '14px 16px', fontWeight: 600 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Database size={16} style={{ color: 'var(--color-accent)' }} />
                        <span>{src.title || 'Official Source Reference'}</span>
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)' }}>
                      {src.source_type || 'Government Portal'}
                    </td>
                    <td style={{ padding: '14px 16px', color: 'var(--color-text-muted)' }}>
                      {src.verified_at ? new Date(src.verified_at).toLocaleDateString() : 'Pending'}
                    </td>
                    <td style={{ padding: '14px 16px', color: 'var(--color-text-muted)' }}>
                      {src.created_at ? new Date(src.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {src.url ? (
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-secondary btn-sm"
                          style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                        >
                          Visit Portal <ExternalLink size={12} />
                        </a>
                      ) : (
                        <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>No URL</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
