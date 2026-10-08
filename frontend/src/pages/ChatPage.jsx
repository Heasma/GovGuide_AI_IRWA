/**
 * GovGuide AI — Citizen-Facing AI Assistant Chat Page
 *
 * Implements robust provider error detection and safe rendering.
 * Never exposes raw [LLM_PROVIDER_ERROR] strings, stack traces, or internal error codes.
 * Ensures confidence, explanations, sources, caveats, and demo badges are ONLY rendered
 * on legitimate, successful AI answers.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { queryService } from '../services/authService'
import { useAuth } from '../context/AuthContext'
import {
  User,
  Bot,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Send,
  Sparkles,
  RefreshCw,
  FileText,
  Info,
} from 'lucide-react'
import ConfidenceBadge from '../components/portal/ConfidenceBadge'
import SourceCard from '../components/portal/SourceCard'
import { getCitizenErrorMessage, isProviderErrorResponse } from '../utils/errorMessages'

// Import assets
import logoMark from '../assets/images/logo_mark.svg'

// ── Constants ──────────────────────────────────────────────────────────

const EXAMPLE_QUERIES = [
  'What documents are required for a business license?',
  'How do I apply for a government service?',
  'Which services are available online?',
  'Where can I apply for this service?',
]

// ── Sub-components ─────────────────────────────────────────────────────

function UserMessage({ content }) {
  return (
    <div className="msg-row msg-row--user fade-in" role="article" aria-label="Your question">
      <div className="msg-avatar msg-avatar--user">
        <User size={15} aria-hidden="true" />
      </div>
      <div className="msg-bubble msg-bubble--user">
        {content}
      </div>
    </div>
  )
}

function CaveatCard({ caveats }) {
  if (!caveats || caveats.length === 0) return null
  return (
    <div className="caveat-card" role="note" aria-label="Important information">
      <div className="caveat-card__header">
        <AlertCircle size={15} aria-hidden="true" />
        <span>Important Information</span>
      </div>
      <ul className="caveat-card__list">
        {caveats.map((c, i) => (
          <li key={i}>{c}</li>
        ))}
      </ul>
    </div>
  )
}

function SourcesSection({ sources }) {
  const [expanded, setExpanded] = useState(false)
  if (!sources || sources.length === 0) return null

  return (
    <div className="sources-section">
      <button
        type="button"
        className="sources-toggle"
        onClick={() => setExpanded(prev => !prev)}
        aria-expanded={expanded}
        aria-controls="sources-panel"
      >
        <span className="sources-toggle__label">
          <FileText size={14} aria-hidden="true" />
          Official Sources ({sources.length})
        </span>
        {expanded ? <ChevronUp size={15} aria-hidden="true" /> : <ChevronDown size={15} aria-hidden="true" />}
      </button>

      {expanded && (
        <div id="sources-panel" className="sources-panel fade-in">
          {sources.map((s, i) => (
            <SourceCard key={s.source_id || i} source={s} index={i + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

function AssistantErrorMessage({ message, onRetry, loading }) {
  return (
    <div className="msg-row msg-row--assistant fade-in" role="alert" aria-label="GovGuide AI error">
      <div className="msg-avatar msg-avatar--assistant msg-avatar--error">
        <AlertCircle size={15} aria-hidden="true" />
      </div>

      <div className="ai-error-card">
        <div className="ai-error-card__header">
          <AlertCircle size={16} className="ai-error-card__icon" aria-hidden="true" />
          <span className="ai-error-card__title">
            {message.errorTitle || 'Unable to generate an answer'}
          </span>
        </div>
        <p className="ai-error-card__message">
          {message.errorMessage || 'GovGuide AI is temporarily unable to generate an answer. Please try again shortly.'}
        </p>
        {onRetry && message.retryQuery && (
          <div className="ai-error-card__action">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => onRetry(message.retryQuery)}
              disabled={loading}
              aria-label="Try submitting your query again"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <RefreshCw size={13} aria-hidden="true" />
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function AssistantMessage({ message, onRetry, loading }) {
  // If this message represents an error response or provider failure
  if (message.isError) {
    return <AssistantErrorMessage message={message} onRetry={onRetry} loading={loading} />
  }

  const data = message.data
  const isConversational = data?.is_conversational === true || (!data?.confidence_label && (!data?.sources || data.sources.length === 0) && (!data?.caveats || data.caveats.length === 0))

  return (
    <div className="msg-row msg-row--assistant fade-in" role="article" aria-label="GovGuide AI response">
      <div className="msg-avatar msg-avatar--assistant">
        <img src={logoMark} alt="" aria-hidden="true" style={{ width: 16, height: 16 }} />
      </div>

      <div className="ai-response-card">
        {/* Demo Mode Badge */}
        {!isConversational && data?.is_demo === true && (
          <div className="demo-mode-badge" role="status">
            <Sparkles size={11} aria-hidden="true" />
            Demo Mode
          </div>
        )}

        {/* Answer */}
        <div className="ai-response-answer">
          {data?.answer || message.content}
        </div>

        {/* ONLY show metadata for substantive government responses */}
        {!isConversational && (
          <>
            {/* Confidence + Explanation (ONLY on successful valid answers) */}
            {data?.confidence_label && (
              <div className="ai-response-confidence">
                <ConfidenceBadge confidenceLabel={data.confidence_label} />
                {data?.explanation && (
                  <p className="explanation-text">
                    <Info size={12} aria-hidden="true" style={{ flexShrink: 0, marginTop: 1 }} />
                    <span>{data.explanation}</span>
                  </p>
                )}
              </div>
            )}

            {/* Caveats */}
            <CaveatCard caveats={data?.caveats} />

            {/* Official Sources */}
            <SourcesSection sources={data?.sources} />

            {/* Responsible AI Footer (per-response) */}
            <div className="responsible-ai-footer" role="note">
              GovGuide AI provides guidance based on available official information. Always verify
              important requirements, fees, deadlines, and legal information with the responsible
              government authority.
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div className="msg-row msg-row--assistant fade-in" role="status" aria-live="polite" aria-label="GovGuide AI is thinking">
      <div className="msg-avatar msg-avatar--assistant">
        <img src={logoMark} alt="" aria-hidden="true" style={{ width: 16, height: 16 }} />
      </div>
      <div className="ai-thinking">
        <div className="ai-thinking__dots" aria-hidden="true">
          <div className="pulse-dot" />
          <div className="pulse-dot" />
          <div className="pulse-dot" />
        </div>
        <span className="ai-thinking__text">Finding official government information...</span>
      </div>
    </div>
  )
}

// ── Hero Section (empty state) ─────────────────────────────────────────

function ChatHero({ inputValue, onInputChange, onSubmit, onExampleClick, loading, inputRef }) {
  return (
    <div className="chat-hero">
      <div className="chat-hero__inner">
        {/* Brand mark */}
        <div className="chat-hero__brand">
          <img src={logoMark} alt="GovGuide AI" className="chat-hero__logo" />
        </div>

        <h1 className="chat-hero__heading">
          Find the Government Service You Need
        </h1>
        <p className="chat-hero__subtext">
          Ask a question in plain language and get guidance based on official government information.
        </p>

        {/* Main input */}
        <form onSubmit={onSubmit} className="chat-hero__form">
          <div className="chat-hero__input-wrap">
            <textarea
              id="hero-query-input"
              ref={inputRef}
              className="chat-hero__textarea"
              value={inputValue}
              onChange={e => onInputChange(e.target.value)}
              placeholder="What government service do you need help with?"
              rows={3}
              disabled={loading}
              aria-label="Enter your government service question"
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  onSubmit(e)
                }
              }}
            />
          </div>
          <button
            id="hero-submit-btn"
            type="submit"
            className="chat-hero__submit btn btn-primary"
            disabled={!inputValue.trim() || loading}
            aria-label="Ask GovGuide AI"
          >
            {loading ? (
              <span className="loading-dots" style={{ margin: '0 auto' }}>
                <span className="loading-dot" />
                <span className="loading-dot" />
                <span className="loading-dot" />
              </span>
            ) : (
              <>
                <Send size={16} aria-hidden="true" />
                Ask GovGuide AI
              </>
            )}
          </button>
        </form>

        {/* Example queries */}
        <div className="query-examples" role="list" aria-label="Example questions">
          <p className="query-examples__label">Try asking:</p>
          <div className="query-examples__chips">
            {EXAMPLE_QUERIES.map((q, i) => (
              <button
                key={i}
                type="button"
                className="query-chip"
                onClick={() => onExampleClick(q)}
                disabled={loading}
                role="listitem"
                aria-label={`Use example: ${q}`}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main ChatPage ──────────────────────────────────────────────────────

export default function ChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [heroError, setHeroError] = useState('')
  const endRef = useRef(null)
  const inputRef = useRef(null)
  const sessionId = useRef(
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `session-${Date.now()}`
  )

  const hasMessages = messages.length > 0

  // Auto-scroll to bottom whenever messages or loading state change
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Focus input on load
  useEffect(() => {
    if (!hasMessages && inputRef.current) {
      inputRef.current.focus()
    }
  }, [hasMessages])

  const handleSend = useCallback(async (explicitQuery) => {
    const query = (typeof explicitQuery === 'string' ? explicitQuery : input).trim()
    if (!query || loading) return

    setInput('')
    setHeroError('')
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: query }])
    setLoading(true)

    try {
      const result = await queryService.submitQuery(query, sessionId.current)

      // ── DETECT BACKEND/PROVIDER ERRORS BEFORE RENDERING ──────────
      if (isProviderErrorResponse(result)) {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          role: 'assistant',
          isError: true,
          errorTitle: 'Unable to generate an answer',
          errorMessage: 'GovGuide AI is temporarily unable to generate an answer. Please try again shortly.',
          retryQuery: query,
        }])
      } else {
        // Legitimate, valid AI response
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          role: 'assistant',
          isError: false,
          content: result.answer,
          data: result,
        }])
      }
    } catch (err) {
      const citizenMsg = getCitizenErrorMessage(err)
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        isError: true,
        errorTitle: 'Unable to generate an answer',
        errorMessage: citizenMsg,
        retryQuery: query,
      }])
    } finally {
      setLoading(false)
    }
  }, [input, loading])

  const handleRetry = useCallback((retryQuery) => {
    if (retryQuery && !loading) {
      handleSend(retryQuery)
    }
  }, [handleSend, loading])

  const handleExampleClick = useCallback((query) => {
    setInput(query)
    inputRef.current?.focus()
  }, [])

  const handleNewQuestion = useCallback(() => {
    setMessages([])
    setInput('')
    setHeroError('')
    sessionId.current = typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `session-${Date.now()}`
  }, [])

  const handleChatKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  return (
    <div className="chat-page fade-in">
      {/* ── Topbar ────────────────────────────────────────────────── */}
      <div className="topbar">
        <div className="topbar-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <Bot size={18} aria-hidden="true" />
          GovGuide AI Assistant
        </div>
        <div className="chat-topbar-actions">
          {hasMessages && (
            <button
              id="new-question-btn"
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleNewQuestion}
              aria-label="Start a new question and clear the current conversation"
            >
              <RefreshCw size={13} aria-hidden="true" />
              New Question
            </button>
          )}
        </div>
      </div>

      {/* ── Empty state: Hero ──────────────────────────────────── */}
      {!hasMessages && (
        <div className="chat-hero-wrapper">
          <ChatHero
            inputValue={input}
            onInputChange={setInput}
            onSubmit={e => { e.preventDefault(); handleSend(); }}
            onExampleClick={handleExampleClick}
            loading={loading}
            inputRef={inputRef}
          />
          {heroError && (
            <div className="citizen-error-msg" role="alert">
              <AlertCircle size={15} aria-hidden="true" />
              <span>{heroError}</span>
            </div>
          )}
        </div>
      )}

      {/* ── Chat state: Messages ───────────────────────────────── */}
      {hasMessages && (
        <>
          <div className="chat-messages" role="log" aria-live="polite" aria-label="Conversation">
            {messages.map(msg =>
              msg.role === 'user'
                ? <UserMessage key={msg.id} content={msg.content} />
                : <AssistantMessage key={msg.id} message={msg} onRetry={handleRetry} loading={loading} />
            )}

            {loading && <ThinkingIndicator />}

            <div ref={endRef} aria-hidden="true" />
          </div>

          {/* ── Chat Input Area ──────────────────────────────── */}
          <div className="chat-input-area">
            <form onSubmit={e => { e.preventDefault(); handleSend(); }}>
              <div className="chat-input-box">
                <textarea
                  id="chat-input"
                  className="chat-textarea"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleChatKeyDown}
                  placeholder="Ask a follow-up question..."
                  rows={1}
                  disabled={loading}
                  aria-label="Enter your follow-up question"
                />
                <button
                  id="chat-send-btn"
                  type="submit"
                  className="chat-send-btn"
                  disabled={!input.trim() || loading}
                  aria-label="Send message"
                >
                  <Send size={14} aria-hidden="true" />
                </button>
              </div>
            </form>
            <div className="chat-hint">
              Press Enter to send · Shift+Enter for new line
            </div>
          </div>
        </>
      )}
    </div>
  )
}
