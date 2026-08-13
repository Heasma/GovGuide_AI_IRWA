import { useState, useRef, useEffect } from 'react'
import { queryService } from '../services/authService'
import { useAuth } from '../context/AuthContext'
import { 
  User, 
  Bot, 
  ShieldCheck, 
  AlertCircle, 
  ExternalLink, 
  ChevronDown, 
  ChevronUp, 
  Send,
  Database,
  FileText
} from 'lucide-react'
import EmptyState from '../components/common/EmptyState'

// Import assets
import logoMark from '../assets/images/logo_mark.svg'
import emptySearchImg from '../assets/illustrations/empty_search.svg'

function ConfidenceBadge({ label }) {
  const labelText = label ? label.toUpperCase() : 'UNKNOWN'
  return (
    <span className={`confidence-badge ${label || 'insufficient'}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      <ShieldCheck size={12} />
      <span>Confidence: {labelText}</span>
    </span>
  )
}

function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false)

  if (message.role === 'user') {
    return (
      <div className="message-row user fade-in">
        <div className="message-avatar user">
          <User size={16} />
        </div>
        <div className="message-bubble">
          <div className="message-content">{message.content}</div>
        </div>
      </div>
    )
  }

  const data = message.data
  const hasSources = data?.sources?.length > 0

  return (
    <div className="message-row assistant fade-in">
      <div className="message-avatar assistant">
        <img src={logoMark} alt="GovGuide AI" style={{ width: 16, height: 16 }} />
      </div>
      <div className="message-bubble" style={{ maxWidth: 700 }}>
        <div className="response-card premium-card" style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          <div className="response-answer" style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-text-primary)' }}>
            {data?.answer || message.content}
          </div>

          {data?.caveats?.length > 0 && (
            <div className="caveats" style={{ marginTop: 16, padding: '12px 16px', background: '#fffbeb', borderLeft: '3px solid #f59e0b', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, fontSize: 12, color: '#d97706', marginBottom: 4 }}>
                <AlertCircle size={14} /> Caveats & Important Context
              </div>
              <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12, color: '#b45309', lineHeight: 1.5 }}>
                {data.caveats.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </div>
          )}

          {/* Collapsible Sources Panel */}
          {hasSources && (
            <div className="sources-container" style={{ marginTop: 20, borderTop: '1px solid var(--color-border)', paddingTop: 12 }}>
              <button 
                type="button" 
                onClick={() => setShowSources(prev => !prev)}
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between', 
                  width: '100%', 
                  color: 'var(--color-text-secondary)',
                  fontSize: 13,
                  fontWeight: 600,
                  padding: '6px 0'
                }}
              >
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <FileText size={15} /> 
                  <span>References & Sources ({data.sources.length})</span>
                </span>
                {showSources ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              {showSources && (
                <div className="source-panel fade-in" style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {data.sources.map((s, i) => (
                    <div key={s.source_id || i} className="source-item" style={{ 
                      padding: 12, 
                      background: 'var(--color-bg)', 
                      border: '1px solid var(--color-border)', 
                      borderRadius: 'var(--radius-sm)',
                      fontSize: 12
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <strong style={{ color: 'var(--color-text-primary)' }}>{i + 1}. {s.title || 'Official Source'}</strong>
                        {s.url && (
                          <a href={s.url} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--color-accent)' }}>
                            Link <ExternalLink size={12} />
                          </a>
                        )}
                      </div>
                      {s.excerpt && <p style={{ margin: 0, color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>{s.excerpt}</p>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="response-footer" style={{ marginTop: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--color-border)', paddingTop: 12 }}>
            {data?.confidence_label && (
              <ConfidenceBadge label={data.confidence_label} />
            )}
            {data?.is_demo && (
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                <AlertCircle size={12} /> Demo mode — dataset pending
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSend = async (e) => {
    e?.preventDefault()
    const query = input.trim()
    if (!query || loading) return

    setInput('')
    setError('')
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: query }])
    setLoading(true)

    try {
      const result = await queryService.submitQuery(query)
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: result.answer,
        data: result,
      }])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get a response. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-page fade-in">
      {/* Header */}
      <div className="topbar">
        <div className="topbar-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <Bot size={18} /> GovGuide AI Assistant
        </div>
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <Database size={12} /> Dataset: Pending
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages" style={{ padding: '24px 16px' }}>
        {messages.length === 0 && (
          <EmptyState
            illustration={emptySearchImg}
            title="Start a conversation with GovGuide AI"
            description="Submit queries about government service discovery, document regulations, procedures, and official guidelines. The agents will process search queries and produce evidence-grounded responses."
            action={
              <div className="demo-banner">
                <AlertCircle size={14} style={{ marginRight: 6 }} />
                <span><strong>Demo Mode</strong> — Stubs will display until the official database is integrated.</span>
              </div>
            }
          />
        )}

        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {loading && (
          <div className="message-row assistant">
            <div className="message-avatar assistant">
              <img src={logoMark} alt="GovGuide AI" style={{ width: 16, height: 16 }} />
            </div>
            <div className="message-bubble">
              <div className="message-content" style={{ padding: '8px 16px' }}>
                <div className="pulse-dots">
                  <div className="pulse-dot" />
                  <div className="pulse-dot" />
                  <div className="pulse-dot" />
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="error-state text-small" style={{ maxWidth: 600, alignSelf: 'center', marginTop: 16 }}>
            <AlertCircle size={14} style={{ marginRight: 6 }} />
            <span>{error}</span>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <form onSubmit={handleSend}>
          <div className="chat-input-box">
            <textarea
              id="chat-input"
              className="chat-textarea"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about a government service, eligibility, or procedure..."
              rows={1}
              disabled={loading}
            />
            <button
              id="chat-send-btn"
              type="submit"
              className="chat-send-btn"
              disabled={!input.trim() || loading}
              aria-label="Send message"
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              <Send size={14} />
            </button>
          </div>
        </form>
        <div className="chat-hint">
          Press Enter to send · Shift+Enter for new line · All responses are evidence-grounded stubs
        </div>
      </div>
    </div>
  )
}
