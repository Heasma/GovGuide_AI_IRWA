/**
 * GovGuide AI — Search Page
 *
 * Functional service search backed by GET /api/v1/services/search.
 * Replaces the old "dataset pending" empty page.
 */

import { useState, useRef, useEffect } from 'react'
import { Search, AlertCircle, Building2, DollarSign, Tag, ChevronRight, RefreshCw, Loader2, ShieldCheck } from 'lucide-react'
import Modal from '../components/common/Modal'
import { governmentService } from '../services/governmentService'

// Re-usable inline service result card (compact variant)
function SearchResultCard({ service, onClick }) {
  const { name, description, category, service_code, fee_amount, office } = service
  return (
    <div
      className="card premium-card"
      style={{ padding: '16px 18px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 6 }}
      onClick={() => onClick(service)}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        {category && category !== 'NOT_AVAILABLE' && (
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-accent)', background: 'rgba(99,102,241,0.1)', padding: '2px 8px', borderRadius: 12 }}>
            {category.replace(/_/g, ' ')}
          </span>
        )}
        {service_code && (
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)', display: 'inline-flex', alignItems: 'center', gap: 3 }}>
            <Tag size={10} /> {service_code}
          </span>
        )}
      </div>

      <h3 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--color-text-primary)' }}>{name}</h3>

      {description && description !== 'NOT_AVAILABLE' && (
        <p style={{ margin: 0, fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {description}
        </p>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
        <div style={{ display: 'flex', gap: 10, fontSize: 12, color: 'var(--color-text-muted)' }}>
          {fee_amount && fee_amount !== 'NOT_AVAILABLE' && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}><DollarSign size={11} />{fee_amount}</span>
          )}
          {office?.name && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}><Building2 size={11} />{office.name}</span>
          )}
        </div>
        <span style={{ fontSize: 12, color: 'var(--color-primary)', display: 'inline-flex', alignItems: 'center', gap: 3 }}>
          Details <ChevronRight size={12} />
        </span>
      </div>
    </div>
  )
}

export default function SearchPage() {
  const [query, setQuery]           = useState('')
  const [activeQuery, setActive]    = useState('')
  const [results, setResults]       = useState([])
  const [total, setTotal]           = useState(0)
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState(null)
  const [searched, setSearched]     = useState(false)
  const [selected, setSelected]     = useState(null)
  const debounceRef                 = useRef(null)

  // Debounced auto-search
  useEffect(() => {
    clearTimeout(debounceRef.current)
    if (!query.trim()) {
      setResults([])
      setTotal(0)
      setSearched(false)
      setActive('')
      return
    }
    debounceRef.current = setTimeout(() => setActive(query.trim()), 400)
    return () => clearTimeout(debounceRef.current)
  }, [query])

  // Fetch when activeQuery changes
  useEffect(() => {
    if (!activeQuery) return
    setLoading(true)
    setError(null)
    governmentService.searchServices(activeQuery, 0, 30)
      .then(res => {
        setResults(res.items || [])
        setTotal(res.total)
        setSearched(true)
      })
      .catch(err => {
        const status = err?.response?.status
        if (status >= 500) setError('A server error occurred. Please try again.')
        else if (!err.response) setError('Unable to connect. Check your internet connection.')
        else setError('Search failed. Please try again.')
      })
      .finally(() => setLoading(false))
  }, [activeQuery])

  const handleSubmit = (e) => {
    e.preventDefault()
    setActive(query.trim())
  }

  return (
    <div style={{ padding: '32px 24px', maxWidth: 900, margin: '0 auto' }} className="fade-in">

      {/* Dataset info banner */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
        background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 8,
        fontSize: 13, color: '#1e40af', marginBottom: 28,
      }}>
        <ShieldCheck size={15} style={{ flexShrink: 0 }} />
        <span>Searching the <strong>City of Chicago Business License Registry</strong> — real data from the active database.</span>
      </div>

      {/* Hero search */}
      <div style={{ textAlign: 'center', marginBottom: 36 }}>
        <h2 className="text-display" style={{ marginBottom: 8 }}>Government License Search</h2>
        <p className="text-body" style={{ color: 'var(--color-text-secondary)', marginBottom: 24, maxWidth: 560, margin: '0 auto 24px' }}>
          Find official Chicago business license types, eligibility requirements, fees, and application procedures.
        </p>

        <form onSubmit={handleSubmit} style={{ maxWidth: 640, margin: '0 auto', display: 'flex', gap: 10 }}>
          <div className="form-input-container" style={{ flex: 1 }}>
            <Search size={18} className="form-input-icon" />
            <input
              id="service-search-input"
              type="text"
              className="search-input form-input-with-icon"
              placeholder="Search license types (e.g. Food, Retail, Childcare)…"
              value={query}
              onChange={e => setQuery(e.target.value)}
              style={{ width: '100%' }}
              autoFocus
              aria-label="Search government services"
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ flexShrink: 0, display: 'inline-flex', alignItems: 'center', gap: 6 }}
            disabled={!query.trim()}
          >
            <Search size={15} /> Search
          </button>
        </form>
      </div>

      {/* Loading */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--color-text-muted)' }}>
          <Loader2 size={28} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 12px', display: 'block' }} />
          <p style={{ fontSize: 14 }}>Searching services…</p>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, fontSize: 13, color: '#991b1b' }}>
          <AlertCircle size={15} style={{ flexShrink: 0 }} /> {error}
        </div>
      )}

      {/* Results */}
      {!loading && !error && searched && (
        <>
          <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 16 }}>
            {total === 0
              ? `No results for "${activeQuery}"`
              : `${total} result${total !== 1 ? 's' : ''} for "${activeQuery}"${total > results.length ? ` — showing ${results.length}` : ''}`
            }
          </div>

          {total === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--color-text-muted)' }}>
              <Building2 size={36} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.3 }} />
              <p style={{ fontSize: 14 }}>No license types matched your search. Try different keywords.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {results.map(svc => (
                <SearchResultCard key={svc.id} service={svc} onClick={setSelected} />
              ))}
            </div>
          )}
        </>
      )}

      {/* Empty / pre-search state */}
      {!loading && !error && !searched && (
        <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--color-text-muted)' }}>
          <Search size={36} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.2 }} />
          <p style={{ fontSize: 14 }}>Type a search term above to find Chicago business license types.</p>
        </div>
      )}

      {/* Detail modal — reuse same fields as GovernmentServicesPage */}
      {selected && (
        <Modal isOpen={!!selected} onClose={() => setSelected(null)} title={selected.name}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {selected.description && selected.description !== 'NOT_AVAILABLE' && (
              <p style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--color-text-secondary)', margin: 0 }}>{selected.description}</p>
            )}
            {[
              ['License Code', selected.service_code],
              ['Category', selected.category?.replace(/_/g, ' ')],
              ['Fee', selected.fee_amount !== 'NOT_AVAILABLE' ? selected.fee_amount : null],
              ['Fee Notes', selected.fee_description !== 'NOT_AVAILABLE' ? selected.fee_description : null],
              ['Eligibility', selected.eligibility_summary !== 'NOT_AVAILABLE' ? selected.eligibility_summary : null],
              ['Required Documents', selected.required_documents !== 'NOT_AVAILABLE' ? selected.required_documents : null],
              ['How to Apply', selected.application_steps !== 'NOT_AVAILABLE' ? selected.application_steps : null],
              ['Renewal Period', selected.renewal_period],
              ['License Term', selected.license_term_years ? `${selected.license_term_years} year(s)` : null],
              ['Legal Reference', selected.legal_reference !== 'NOT_AVAILABLE' ? selected.legal_reference : null],
              ['Issuing Authority', selected.office?.name],
              ['Department', selected.office?.department],
              ['Phone', selected.office?.phone],
              ['Business Hours', selected.office?.business_hours],
            ].map(([label, val]) => val && (
              <div key={label} style={{ display: 'flex', gap: 12, paddingBottom: 8, borderBottom: '1px solid var(--color-border-light)' }}>
                <span style={{ minWidth: 150, fontSize: 12, color: 'var(--color-text-muted)', fontWeight: 600 }}>{label}</span>
                <span style={{ fontSize: 13, color: 'var(--color-text-primary)', flex: 1, lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{val}</span>
              </div>
            ))}
            <div style={{ display: 'flex', gap: 10, marginTop: 8, flexWrap: 'wrap' }}>
              {selected.application_portal_url && selected.application_portal_url !== 'NOT_AVAILABLE' && (
                <a href={selected.application_portal_url} target="_blank" rel="noopener noreferrer" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  Apply Online <RefreshCw size={13} />
                </a>
              )}
              {selected.source_url && selected.source_url !== 'NOT_AVAILABLE' && (
                <a href={selected.source_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  Official Source <ChevronRight size={13} />
                </a>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
