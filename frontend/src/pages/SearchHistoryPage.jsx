/**
 * GovGuide AI — Recent Query History Page
 *
 * Backed by real session data from GET /api/v1/sessions.
 * Explains that query history is derived from active database AI conversation sessions.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../components/common/PageHeader'
import SearchBar from '../components/common/SearchBar'
import { sessionService } from '../services/sessionService'
import {
  History,
  MessageSquare,
  Clock,
  Trash2,
  AlertCircle,
  Loader2,
  ExternalLink,
  Bot,
  RefreshCw,
} from 'lucide-react'

export default function SearchHistoryPage() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  const fetchSessions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await sessionService.listSessions()
      setSessions(data || [])
    } catch (err) {
      const status = err?.response?.status
      if (status >= 500) setError('A server error occurred while retrieving query history.')
      else if (!err.response) setError('Unable to connect to the server. Please check your network.')
      else setError('Failed to load query history.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  const handleDelete = async (sessionId) => {
    if (!window.confirm('Delete this conversation record from the database?')) return
    try {
      await sessionService.deleteSession(sessionId)
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId))
    } catch {
      alert('Failed to delete query session.')
    }
  }

  const filteredSessions = sessions.filter((s) =>
    s.session_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (s.started_at && new Date(s.started_at).toLocaleString().toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader
        title="Recent Query History"
        subtitle="Historical AI conversation sessions and service inquiry logs recorded in the database."
      />

      {/* Info notice explaining database source */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px',
        background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 8,
        fontSize: 13, color: '#1e40af', marginBottom: 24,
      }}>
        <History size={16} style={{ flexShrink: 0 }} />
        <span>
          Query history is derived from active <strong>query_sessions</strong> in PostgreSQL. Each entry corresponds to an authenticated AI assistant dialogue.
        </span>
      </div>

      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <SearchBar
            value={searchTerm}
            onChange={setSearchTerm}
            onClear={() => setSearchTerm('')}
            placeholder="Search query sessions by session ID or date..."
          />
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={fetchSessions}
          title="Refresh history"
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, height: 40 }}
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--color-text-muted)' }}>
          <Loader2 size={28} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 12px', display: 'block' }} />
          <p style={{ fontSize: 14 }}>Loading query history...</p>
        </div>
      )}

      {!loading && error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, fontSize: 13, color: '#991b1b', marginBottom: 24 }}>
          <AlertCircle size={15} style={{ flexShrink: 0 }} /> {error}
        </div>
      )}

      {!loading && !error && filteredSessions.length === 0 && (
        <div style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--color-text-muted)' }}>
          <History size={40} style={{ margin: '0 auto 16px', display: 'block', opacity: 0.25 }} />
          <p style={{ fontSize: 15, fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 6 }}>
            {searchTerm ? 'No matching query sessions found.' : 'No query history recorded yet.'}
          </p>
          <p style={{ fontSize: 13, maxWidth: 460, margin: '0 auto 16px' }}>
            Queries submitted to GovGuide AI will automatically appear in your session history.
          </p>
          {!searchTerm && (
            <button
              className="btn btn-primary btn-sm"
              onClick={() => navigate('/chat')}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <Bot size={14} /> Ask a Question
            </button>
          )}
        </div>
      )}

      {!loading && !error && filteredSessions.length > 0 && (
        <div className="card premium-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'var(--color-surface-2)', borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Session Reference</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Origin</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Started Timestamp</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredSessions.map((item) => {
                  const dateStr = item.started_at
                    ? new Date(item.started_at).toLocaleString()
                    : 'Unknown'

                  return (
                    <tr key={item.session_id} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                      <td style={{ padding: '14px 16px', fontWeight: 600 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <MessageSquare size={15} style={{ color: 'var(--color-primary)' }} />
                          <code style={{ fontSize: 12 }}>{item.session_id.substring(0, 18)}...</code>
                        </div>
                      </td>
                      <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)' }}>
                        AI Assistant / Query Engine
                      </td>
                      <td style={{ padding: '14px 16px', color: 'var(--color-text-muted)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <Clock size={12} /> {dateStr}
                        </div>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{ fontSize: 11, background: '#f0fdf4', color: 'var(--color-success)', padding: '2px 8px', borderRadius: 12, fontWeight: 600, border: '1px solid #bbf7d0' }}>
                          Logged in DB
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}>
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => navigate('/conversations')}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                          >
                            Open <ExternalLink size={12} />
                          </button>
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => handleDelete(item.session_id)}
                            title="Delete session record"
                            style={{ color: 'var(--color-danger)' }}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
