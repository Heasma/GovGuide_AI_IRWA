/**
 * GovGuide AI — AI Conversation History Page
 *
 * Fully database-driven using GET /api/v1/sessions and GET /api/v1/sessions/{id}/messages.
 * Zero hardcoded/mock conversation data.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../components/common/PageHeader'
import SearchBar from '../components/common/SearchBar'
import Modal from '../components/common/Modal'
import { sessionService } from '../services/sessionService'
import {
  MessageSquare,
  Clock,
  Bot,
  User,
  Trash2,
  AlertCircle,
  Loader2,
  ExternalLink,
  Plus,
  RefreshCw,
} from 'lucide-react'

export default function ConversationsPage() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  // Modal / message detail state
  const [selectedSession, setSelectedSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [messagesError, setMessagesError] = useState(null)

  // Deletion state
  const [deletingId, setDeletingId] = useState(null)
  const [sessionToDelete, setSessionToDelete] = useState(null)

  const fetchSessions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await sessionService.listSessions()
      setSessions(data || [])
    } catch (err) {
      const status = err?.response?.status
      if (status >= 500) setError('A server error occurred while retrieving sessions.')
      else if (!err.response) setError('Unable to connect to the server. Please check your network.')
      else setError('Failed to load conversation history.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  const handleOpenSession = async (session) => {
    setSelectedSession(session)
    setMessages([])
    setLoadingMessages(true)
    setMessagesError(null)

    try {
      const msgData = await sessionService.getSessionMessages(session.session_id)
      setMessages(msgData || [])
    } catch (err) {
      setMessagesError('Unable to load messages for this conversation.')
    } finally {
      setLoadingMessages(false)
    }
  }

  const handleDeleteSession = async (sessionId) => {
    setDeletingId(sessionId)
    try {
      await sessionService.deleteSession(sessionId)
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId))
      if (selectedSession?.session_id === sessionId) {
        setSelectedSession(null)
      }
      setSessionToDelete(null)
    } catch (err) {
      alert('Failed to delete session. Please try again.')
    } finally {
      setDeletingId(null)
    }
  }

  const filteredSessions = sessions.filter((s) =>
    s.session_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (s.started_at && new Date(s.started_at).toLocaleString().toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <PageHeader
          title="AI Conversation History"
          subtitle="Review and manage your real-time agentic AI consultation logs and dialogue sessions."
        />
        <button
          className="btn btn-primary"
          onClick={() => navigate('/chat')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
        >
          <Plus size={16} /> New AI Inquiry
        </button>
      </div>

      <div style={{ marginBottom: 24, display: 'flex', gap: 12, alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <SearchBar
            value={searchTerm}
            onChange={setSearchTerm}
            onClear={() => setSearchTerm('')}
            placeholder="Search sessions by ID or date..."
          />
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={fetchSessions}
          title="Refresh sessions"
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, height: 40 }}
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--color-text-muted)' }}>
          <Loader2 size={28} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 12px', display: 'block' }} />
          <p style={{ fontSize: 14 }}>Loading conversation history...</p>
        </div>
      )}

      {!loading && error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, fontSize: 13, color: '#991b1b', marginBottom: 24 }}>
          <AlertCircle size={15} style={{ flexShrink: 0 }} /> {error}
          <button className="btn btn-ghost btn-sm" onClick={fetchSessions} style={{ marginLeft: 'auto' }}>Retry</button>
        </div>
      )}

      {!loading && !error && filteredSessions.length === 0 && (
        <div style={{ textAlign: 'center', padding: '64px 24px', color: 'var(--color-text-muted)' }}>
          <MessageSquare size={48} style={{ margin: '0 auto 16px', display: 'block', opacity: 0.25 }} />
          <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
            {searchTerm ? 'No matching conversations found.' : 'No conversation sessions yet.'}
          </h3>
          <p style={{ fontSize: 14, maxWidth: 460, margin: '0 auto 20px', lineHeight: 1.6 }}>
            {searchTerm
              ? 'Try changing your search keywords or clear the filter.'
              : 'Interact with GovGuide AI via the Assistant to start an evidence-grounded research dialogue.'}
          </p>
          {!searchTerm && (
            <button
              className="btn btn-primary"
              onClick={() => navigate('/chat')}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <Bot size={16} /> Launch Assistant
            </button>
          )}
        </div>
      )}

      {!loading && !error && filteredSessions.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20 }}>
          {filteredSessions.map((session) => {
            const formattedDate = session.started_at
              ? new Date(session.started_at).toLocaleString(undefined, {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })
              : 'Unknown date'

            return (
              <div
                key={session.session_id}
                className="card premium-card"
                style={{ display: 'flex', flexDirection: 'column', padding: 20, cursor: 'pointer', transition: 'all 0.2s ease' }}
                onClick={() => handleOpenSession(session)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-accent)', background: 'rgba(99, 102, 241, 0.1)', padding: '3px 8px', borderRadius: 4, fontFamily: 'monospace' }}>
                    ID: {session.session_id.substring(0, 8)}...
                  </span>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      setSessionToDelete(session.session_id)
                    }}
                    title="Delete session"
                    style={{ color: 'var(--color-danger)', padding: 4 }}
                  >
                    <Trash2 size={15} />
                  </button>
                </div>

                <h3 className="text-h2" style={{ fontSize: 15, fontWeight: 700, marginBottom: 8, color: 'var(--color-text-primary)' }}>
                  Session {session.session_id.substring(0, 13)}
                </h3>

                <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', background: 'var(--color-surface-2)', padding: '8px 12px', borderRadius: 6, marginBottom: 14 }}>
                  Stored in PostgreSQL query sessions database.
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: 'var(--color-text-muted)', borderTop: '1px solid var(--color-border)', paddingTop: 12 }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    <Clock size={13} /> {formattedDate}
                  </span>
                  <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>View Dialogue →</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Messages Detail Modal */}
      <Modal
        isOpen={!!selectedSession}
        onClose={() => setSelectedSession(null)}
        title={selectedSession ? `Session ${selectedSession.session_id.substring(0, 13)}` : 'Conversation Details'}
      >
        {selectedSession && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxHeight: '65vh', overflowY: 'auto' }}>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', paddingBottom: 8, borderBottom: '1px solid var(--color-border)' }}>
              Started: {new Date(selectedSession.started_at).toLocaleString()} | Full Session ID: <code>{selectedSession.session_id}</code>
            </div>

            {loadingMessages && (
              <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--color-text-muted)' }}>
                <Loader2 size={24} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 8px', display: 'block' }} />
                <span>Loading messages from database...</span>
              </div>
            )}

            {!loadingMessages && messagesError && (
              <div style={{ padding: 12, background: '#fef2f2', color: '#991b1b', borderRadius: 6, fontSize: 13 }}>
                {messagesError}
              </div>
            )}

            {!loadingMessages && !messagesError && messages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--color-text-muted)', fontSize: 13 }}>
                No message records found in this session.
              </div>
            )}

            {!loadingMessages && !messagesError && messages.map((msg, i) => {
              const isUser = msg.role === 'user'
              return (
                <div
                  key={msg.message_id || i}
                  style={{
                    display: 'flex',
                    gap: 12,
                    alignItems: 'flex-start',
                    background: isUser ? 'var(--color-surface-2)' : 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    padding: 14,
                    borderRadius: 8,
                  }}
                >
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: '50%',
                      background: isUser ? '#2563eb' : '#7c3aed',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    {isUser ? <User size={14} /> : <Bot size={14} />}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-text-primary)' }}>
                        {isUser ? 'User Query' : 'GovGuide AI Response'}
                      </span>
                      {msg.created_at && (
                        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                          {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!sessionToDelete}
        onClose={() => setSessionToDelete(null)}
        title="Confirm Deletion"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <p style={{ margin: 0, fontSize: 14, color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
            Are you sure you want to delete this session and all its associated conversation messages? This action cannot be undone.
          </p>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
            <button
              className="btn btn-secondary"
              onClick={() => setSessionToDelete(null)}
              disabled={deletingId !== null}
            >
              Cancel
            </button>
            <button
              className="btn btn-primary"
              style={{ background: 'var(--color-danger)', borderColor: 'var(--color-danger)' }}
              onClick={() => handleDeleteSession(sessionToDelete)}
              disabled={deletingId !== null}
            >
              {deletingId ? 'Deleting...' : 'Delete Session'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
