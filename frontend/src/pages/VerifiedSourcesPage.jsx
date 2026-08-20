/**
 * GovGuide AI — Verified Sources Dashboard Page
 *
 * Grounded in real official sources data from the database.
 * Displays 0 counts and honest state when no sources are populated.
 * Zero fabricated percentages or reliability scores.
 */

import { useState, useEffect } from 'react'
import PageHeader from '../components/common/PageHeader'
import StatCard from '../components/common/StatCard'
import { governmentService } from '../services/governmentService'
import {
  ShieldCheck,
  Database,
  CheckCircle,
  Clock,
  ExternalLink,
  Loader2,
  AlertCircle,
} from 'lucide-react'

export default function VerifiedSourcesPage() {
  const [sources, setSources] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    governmentService.listSources(0, 100)
      .then((data) => {
        setSources(data?.items || [])
        setTotal(data?.total || 0)
      })
      .catch((err) => {
        const status = err?.response?.status
        if (status >= 500) setError('A server error occurred.')
        else if (!err.response) setError('Unable to connect to the server.')
        else setError('Failed to retrieve verified sources ledger.')
      })
      .finally(() => setLoading(false))
  }, [])

  const verifiedSources = sources.filter((s) => s.verified_at)
  const pendingSources = sources.filter((s) => !s.verified_at)

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader
        title="Verified Sources Dashboard"
        subtitle="Cryptographic & administrative verification ledger for official government domain references."
      />

      {/* Real KPI cards */}
      <div className="stat-grid" style={{ marginBottom: 32, gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
        <StatCard title="Total Sources" value={total} icon={Database} color="blue" subtext="Database records" />
        <StatCard title="Verified Sources" value={verifiedSources.length} icon={CheckCircle} color="green" subtext="Cryptographically stamped" />
        <StatCard title="Pending Review" value={pendingSources.length} icon={Clock} color="amber" subtext="Awaiting audit" />
        <StatCard title="Ledger Status" value={total > 0 ? 'Active' : 'Unseeded'} icon={ShieldCheck} color="indigo" subtext="PostgreSQL registry" />
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--color-text-muted)' }}>
          <Loader2 size={28} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 12px', display: 'block' }} />
          <p style={{ fontSize: 14 }}>Auditing official sources ledger...</p>
        </div>
      )}

      {!loading && error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, fontSize: 13, color: '#991b1b', marginBottom: 24 }}>
          <AlertCircle size={15} style={{ flexShrink: 0 }} /> {error}
        </div>
      )}

      {!loading && !error && sources.length === 0 && (
        <div className="card premium-card" style={{ padding: 48, textAlign: 'center', color: 'var(--color-text-muted)' }}>
          <ShieldCheck size={48} style={{ margin: '0 auto 16px', display: 'block', opacity: 0.25 }} />
          <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
            No verified sources registered in the database.
          </h3>
          <p style={{ fontSize: 14, maxWidth: 500, margin: '0 auto', lineHeight: 1.6 }}>
            The <strong>official_sources</strong> table currently holds 0 entries.
            When verified government domains (e.g. <code>chicago.gov</code>) and regulatory gazettes are added, their verification signatures will be displayed in this ledger.
          </p>
        </div>
      )}

      {!loading && !error && sources.length > 0 && (
        <div className="card premium-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', fontWeight: 700, fontSize: 16 }}>
            Official Source Verification Ledger
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'var(--color-surface-2)', borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Source Domain</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Type</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Verified Date</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((src) => (
                  <tr key={src.id} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                    <td style={{ padding: '14px 16px', fontWeight: 600 }}>{src.title || 'Government Source'}</td>
                    <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)' }}>{src.source_type || 'Portal'}</td>
                    <td style={{ padding: '14px 16px', color: 'var(--color-text-muted)' }}>
                      {src.verified_at ? new Date(src.verified_at).toLocaleDateString() : 'Unverified'}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{ fontSize: 11, fontWeight: 600, color: src.verified_at ? 'var(--color-success)' : '#d97706', background: src.verified_at ? '#f0fdf4' : '#fffbeb', padding: '2px 8px', borderRadius: 12 }}>
                        {src.verified_at ? 'Verified' : 'Pending'}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {src.url && (
                        <a href={src.url} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          Inspect <ExternalLink size={12} />
                        </a>
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
