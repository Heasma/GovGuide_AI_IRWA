/**
 * GovGuide AI — Government Services Page
 *
 * Fully database-driven. All data comes from the backend API.
 * No hardcoded service arrays. Categories generated dynamically.
 * Search queries the real backend with debounce.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import PageHeader from '../components/common/PageHeader'
import SearchBar from '../components/common/SearchBar'
import Modal from '../components/common/Modal'
import { governmentService } from '../services/governmentService'
import {
  Building2,
  ExternalLink,
  ChevronRight,
  AlertCircle,
  RefreshCw,
  DollarSign,
  Clock,
  FileText,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Phone,
  Mail,
  Globe,
  MapPin,
  Tag,
  Loader2,
} from 'lucide-react'

// ── Helper: map source_confidence to display label ────────────────────────────
function ConfidenceLabel({ value }) {
  if (!value) return null
  const map = {
    VERIFIED: { label: 'Verified', color: 'var(--color-success)', bg: '#f0fdf4' },
    PARTIALLY_VERIFIED: { label: 'Partially Verified', color: '#d97706', bg: '#fffbeb' },
    REQUIRES_MANUAL_VERIFICATION: { label: 'Needs Verification', color: 'var(--color-text-muted)', bg: 'var(--color-surface-2)' },
  }
  const conf = map[value] || { label: value, color: 'var(--color-text-muted)', bg: 'var(--color-surface-2)' }
  return (
    <span style={{
      fontSize: 11, fontWeight: 600,
      color: conf.color, background: conf.bg,
      padding: '2px 8px', borderRadius: 12,
      border: `1px solid ${conf.color}33`,
      display: 'inline-block',
    }}>
      {conf.label}
    </span>
  )
}

// ── Helper: display a boolean field ──────────────────────────────────────────
function BoolBadge({ value, trueLabel = 'Yes', falseLabel = 'No' }) {
  if (value === null || value === undefined) return <span style={{ color: 'var(--color-text-muted)' }}>—</span>
  return value
    ? <span style={{ color: 'var(--color-success)', display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 13 }}><CheckCircle2 size={13} />{trueLabel}</span>
    : <span style={{ color: 'var(--color-text-muted)', display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 13 }}><XCircle size={13} />{falseLabel}</span>
}

// ── Detail row helper ─────────────────────────────────────────────────────────
function DetailRow({ label, value, mono = false }) {
  if (!value && value !== false && value !== 0) return null
  return (
    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', padding: '6px 0', borderBottom: '1px solid var(--color-border-light)' }}>
      <span style={{ minWidth: 160, fontSize: 12, color: 'var(--color-text-muted)', fontWeight: 600, paddingTop: 1 }}>{label}</span>
      <span style={{ fontSize: 13, color: 'var(--color-text-primary)', fontFamily: mono ? 'monospace' : 'inherit', flex: 1, lineHeight: 1.5 }}>
        {typeof value === 'boolean' ? <BoolBadge value={value} /> : String(value)}
      </span>
    </div>
  )
}

// ── Section divider ────────────────────────────────────────────────────────────
function ModalSection({ title, icon: Icon, children }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 10, paddingBottom: 6, borderBottom: '2px solid var(--color-border)' }}>
        <Icon size={15} style={{ color: 'var(--color-primary)' }} />
        <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-text-primary)' }}>{title}</span>
      </div>
      {children}
    </div>
  )
}

// ── Loading skeleton ───────────────────────────────────────────────────────────
function ServiceSkeleton() {
  return (
    <div className="card premium-card" style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
      {[80, 50, 100, 60].map((w, i) => (
        <div key={i} className="skeleton" style={{ height: i === 0 ? 20 : 14, width: `${w}%`, borderRadius: 4 }} />
      ))}
    </div>
  )
}

// ── Service Card ───────────────────────────────────────────────────────────────
function ServiceCard({ service, onClick }) {
  const {
    name, description, category, service_code,
    fee_amount, renewal_required, inspection_required,
    office, source_confidence, is_active,
  } = service

  return (
    <div
      className="card premium-card"
      style={{ display: 'flex', flexDirection: 'column', padding: 20, cursor: 'pointer', transition: 'box-shadow 0.2s' }}
      onClick={() => onClick(service)}
      role="article"
      aria-label={`Service: ${name}`}
    >
      {/* Top meta row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, marginBottom: 10 }}>
        {category && category !== 'NOT_AVAILABLE' && (
          <span style={{
            fontSize: 11, fontWeight: 700, color: 'var(--color-accent)',
            background: 'rgba(99,102,241,0.1)', padding: '3px 8px', borderRadius: 12,
            textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap',
          }}>
            {category.replace(/_/g, ' ')}
          </span>
        )}
        {!is_active && (
          <span style={{ fontSize: 11, color: '#dc2626', background: '#fef2f2', padding: '3px 8px', borderRadius: 12, fontWeight: 600, marginLeft: 'auto' }}>Inactive</span>
        )}
      </div>

      {/* Name */}
      <h3 className="text-h2" style={{ fontSize: 15, fontWeight: 700, margin: '0 0 6px', color: 'var(--color-text-primary)', lineHeight: 1.35 }}>
        {name}
      </h3>

      {/* Description */}
      {description && description !== 'NOT_AVAILABLE' && (
        <p className="text-small" style={{ color: 'var(--color-text-secondary)', fontSize: 13, lineHeight: 1.55, flex: 1, marginBottom: 12, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {description}
        </p>
      )}

      {/* Key facts row */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 14 }}>
        {service_code && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <Tag size={12} style={{ color: 'var(--color-text-muted)' }} />
            Code {service_code}
          </span>
        )}
        {fee_amount && fee_amount !== 'NOT_AVAILABLE' && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <DollarSign size={12} style={{ color: 'var(--color-text-muted)' }} />
            {fee_amount}
          </span>
        )}
        {renewal_required !== null && renewal_required !== undefined && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <RefreshCw size={12} style={{ color: 'var(--color-text-muted)' }} />
            {renewal_required ? 'Renewal required' : 'No renewal'}
          </span>
        )}
        {inspection_required !== null && inspection_required !== undefined && inspection_required && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#b45309' }}>
            <ShieldCheck size={12} />
            Inspection required
          </span>
        )}
      </div>

      {/* Office / authority */}
      {office?.name && (
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 12, display: 'inline-flex', alignItems: 'center', gap: 5 }}>
          <Building2 size={12} />
          {office.name}
        </div>
      )}

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--color-border-light)', paddingTop: 12 }}>
        <ConfidenceLabel value={source_confidence} />
        <button
          className="btn btn-secondary btn-sm"
          onClick={e => { e.stopPropagation(); onClick(service) }}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}
        >
          View Details <ChevronRight size={13} />
        </button>
      </div>
    </div>
  )
}

// ── Service Detail Modal ───────────────────────────────────────────────────────
function ServiceDetailModal({ service, onClose }) {
  if (!service) return null

  const {
    name, description, category, service_code,
    fee_amount, fee_description,
    eligibility_summary, required_documents, application_steps,
    application_portal_url, source_url,
    inspection_required, renewal_required, renewal_period,
    license_term_years, legal_reference, source_confidence,
    office,
  } = service

  const NA = (v) => (!v || v === 'NOT_AVAILABLE') ? null : v

  return (
    <Modal isOpen={!!service} onClose={onClose} title={name}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>

        {/* Header meta */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 20 }}>
          {category && category !== 'NOT_AVAILABLE' && (
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-accent)', background: 'rgba(99,102,241,0.1)', padding: '3px 10px', borderRadius: 12 }}>
              {category.replace(/_/g, ' ')}
            </span>
          )}
          {service_code && <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>License Code: <strong>{service_code}</strong></span>}
          <ConfidenceLabel value={source_confidence} />
        </div>

        {/* 1. Overview */}
        {NA(description) && (
          <ModalSection title="Overview" icon={FileText}>
            <p style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--color-text-secondary)', margin: 0 }}>{description}</p>
          </ModalSection>
        )}

        {/* 2. License Information */}
        {(license_term_years || legal_reference) && (
          <ModalSection title="License Information" icon={ShieldCheck}>
            <DetailRow label="License Term" value={license_term_years ? `${license_term_years} year(s)` : null} />
            <DetailRow label="Legal Reference" value={NA(legal_reference)} />
          </ModalSection>
        )}

        {/* 3. Fee Information */}
        {(NA(fee_amount) || NA(fee_description)) && (
          <ModalSection title="Fee Information" icon={DollarSign}>
            <DetailRow label="Fee Amount" value={NA(fee_amount)} />
            <DetailRow label="Fee Notes" value={NA(fee_description)} />
          </ModalSection>
        )}

        {/* 4. Eligibility */}
        {NA(eligibility_summary) && (
          <ModalSection title="Eligibility" icon={CheckCircle2}>
            <p style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--color-text-secondary)', margin: 0 }}>{eligibility_summary}</p>
          </ModalSection>
        )}

        {/* 5. Required Documents */}
        {NA(required_documents) && (
          <ModalSection title="Required Documents" icon={FileText}>
            <div style={{ fontSize: 13, lineHeight: 1.75, color: 'var(--color-text-secondary)', whiteSpace: 'pre-wrap' }}>
              {required_documents}
            </div>
          </ModalSection>
        )}

        {/* 6. How to Apply */}
        {NA(application_steps) && (
          <ModalSection title="How to Apply" icon={ChevronRight}>
            <div style={{ fontSize: 13, lineHeight: 1.75, color: 'var(--color-text-secondary)', whiteSpace: 'pre-wrap' }}>
              {application_steps}
            </div>
          </ModalSection>
        )}

        {/* 7. Renewal */}
        {(renewal_required !== null && renewal_required !== undefined) && (
          <ModalSection title="Renewal Information" icon={RefreshCw}>
            <DetailRow label="Renewal Required" value={<BoolBadge value={renewal_required} />} />
            <DetailRow label="Renewal Period" value={NA(renewal_period)} />
          </ModalSection>
        )}

        {/* 8. Inspection */}
        {(inspection_required !== null && inspection_required !== undefined) && (
          <ModalSection title="Inspection Requirements" icon={ShieldCheck}>
            <DetailRow label="Inspection Required" value={<BoolBadge value={inspection_required} trueLabel="Yes — inspection needed" falseLabel="No inspection" />} />
          </ModalSection>
        )}

        {/* 9. Issuing Authority */}
        {office && (
          <ModalSection title="Issuing Authority" icon={Building2}>
            {office.name && <DetailRow label="Authority" value={office.name} />}
            {office.department && <DetailRow label="Department" value={office.department} />}
            {(office.street_address || office.city) && (
              <DetailRow
                label="Address"
                value={[office.street_address, office.city, office.state, office.zip_code].filter(Boolean).join(', ')}
              />
            )}
            {office.phone && <DetailRow label="Phone" value={office.phone} />}
            {office.email && <DetailRow label="Email" value={office.email} />}
            {office.business_hours && <DetailRow label="Business Hours" value={office.business_hours} />}
          </ModalSection>
        )}

        {/* 10. Official Source */}
        {NA(source_url) && (
          <ModalSection title="Official Source" icon={Globe}>
            <a
              href={source_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 13, color: 'var(--color-primary)', wordBreak: 'break-all', display: 'inline-flex', alignItems: 'center', gap: 5 }}
            >
              {source_url} <ExternalLink size={12} />
            </a>
          </ModalSection>
        )}

        {/* CTA Buttons */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 8 }}>
          {NA(application_portal_url) && (
            <a
              href={application_portal_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}
            >
              Apply Online <ExternalLink size={14} />
            </a>
          )}
          {NA(source_url) && (
            <a
              href={source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}
            >
              View Official Source <ExternalLink size={14} />
            </a>
          )}
        </div>

      </div>
    </Modal>
  )
}

// ── Empty state ────────────────────────────────────────────────────────────────
function EmptySearchState({ query }) {
  return (
    <div style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--color-text-muted)' }}>
      <Building2 size={40} style={{ margin: '0 auto 16px', opacity: 0.3, display: 'block' }} />
      <p style={{ fontSize: 15, fontWeight: 600, marginBottom: 6, color: 'var(--color-text-secondary)' }}>
        {query ? `No services found for "${query}"` : 'No government services available.'}
      </p>
      <p style={{ fontSize: 13 }}>Try a different search term or category filter.</p>
    </div>
  )
}

// ── Error state ────────────────────────────────────────────────────────────────
function ErrorState({ message, onRetry }) {
  return (
    <div style={{ textAlign: 'center', padding: '48px 24px' }}>
      <AlertCircle size={36} style={{ color: 'var(--color-danger)', margin: '0 auto 12px', display: 'block' }} />
      <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 16 }}>{message}</p>
      <button className="btn btn-secondary btn-sm" onClick={onRetry} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        <RefreshCw size={13} /> Retry
      </button>
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────────
const INITIAL_LIMIT = 24

export default function GovernmentServicesPage() {
  const [services, setServices]         = useState([])
  const [total, setTotal]               = useState(0)
  const [categories, setCategories]     = useState([])
  const [selectedCategory, setCategory] = useState('All')
  const [searchTerm, setSearchTerm]     = useState('')
  const [activeSearch, setActiveSearch] = useState('')
  const [skip, setSkip]                 = useState(0)
  const [loading, setLoading]           = useState(true)
  const [loadingMore, setLoadingMore]   = useState(false)
  const [error, setError]               = useState(null)
  const [selectedService, setSelected]  = useState(null)
  const debounceRef                     = useRef(null)

  // ── Load categories once ───────────────────────────────────────────────────
  useEffect(() => {
    governmentService.getCategories()
      .then(res => setCategories(res.categories || []))
      .catch(() => {}) // non-fatal
  }, [])

  // ── Debounce search input ─────────────────────────────────────────────────
  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setActiveSearch(searchTerm)
      setSkip(0)
    }, 350)
    return () => clearTimeout(debounceRef.current)
  }, [searchTerm])

  // ── Reset pagination when filter changes ──────────────────────────────────
  useEffect(() => { setSkip(0) }, [selectedCategory])

  // ── Fetch services ────────────────────────────────────────────────────────
  const fetchServices = useCallback(async (append = false) => {
    const isSearch = activeSearch.trim().length > 0
    const currentSkip = append ? skip : 0
    if (!append) setLoading(true)
    else setLoadingMore(true)
    setError(null)

    try {
      let res
      if (isSearch) {
        res = await governmentService.searchServices(activeSearch, currentSkip, INITIAL_LIMIT)
      } else {
        res = await governmentService.listServices(
          currentSkip,
          INITIAL_LIMIT,
          selectedCategory !== 'All' ? selectedCategory : null
        )
      }
      setTotal(res.total)
      setServices(prev => append ? [...prev, ...(res.items || [])] : (res.items || []))
      if (!append) setSkip(res.items?.length || 0)
      else setSkip(prev => prev + (res.items?.length || 0))
    } catch (err) {
      const status = err?.response?.status
      if (status >= 500) setError('A server error occurred. Please try again.')
      else if (!err.response) setError('Unable to connect. Please check your connection.')
      else setError('An error occurred while loading services.')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [activeSearch, selectedCategory, skip])

  // Re-fetch when search/category changes (reset)
  useEffect(() => { fetchServices(false) }, [activeSearch, selectedCategory]) // eslint-disable-line

  const handleLoadMore = () => fetchServices(true)

  const hasMore = services.length < total

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader
        title="Chicago Business License Catalogue"
        subtitle="Official City of Chicago business license types, fees, requirements, and application procedures."
      />

      {/* Dataset note */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
        background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 8,
        fontSize: 13, color: '#1e40af', marginBottom: 24,
      }}>
        <ShieldCheck size={15} style={{ flexShrink: 0 }} />
        <span>Data sourced from the City of Chicago Business License Registry. {total > 0 && `${total} license types available.`}</span>
      </div>

      {/* Search + Category Filters */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 28 }}>
        <SearchBar
          value={searchTerm}
          onChange={setSearchTerm}
          onClear={() => setSearchTerm('')}
          placeholder="Search by service name, category, or license code..."
        />

        <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 }}>
          {/* "All" chip */}
          <button
            key="All"
            onClick={() => setCategory('All')}
            className={`btn btn-sm ${selectedCategory === 'All' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ borderRadius: 20, whiteSpace: 'nowrap' }}
          >
            All
          </button>
          {/* Dynamic category chips from real DB */}
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => { setCategory(cat); setSearchTerm('') }}
              className={`btn btn-sm ${selectedCategory === cat ? 'btn-primary' : 'btn-secondary'}`}
              style={{ borderRadius: 20, whiteSpace: 'nowrap', textTransform: 'capitalize' }}
            >
              {cat.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      {loading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
          {Array.from({ length: 6 }).map((_, i) => <ServiceSkeleton key={i} />)}
        </div>
      )}

      {!loading && error && (
        <ErrorState message={error} onRetry={() => fetchServices(false)} />
      )}

      {!loading && !error && services.length === 0 && (
        <EmptySearchState query={activeSearch} />
      )}

      {!loading && !error && services.length > 0 && (
        <>
          {/* Results count */}
          <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 16 }}>
            Showing {services.length} of {total} license{total !== 1 ? 's' : ''}
            {activeSearch && ` matching "${activeSearch}"`}
            {selectedCategory !== 'All' && ` in "${selectedCategory.replace(/_/g, ' ')}"`}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20, marginBottom: 28 }}>
            {services.map(svc => (
              <ServiceCard key={svc.id} service={svc} onClick={setSelected} />
            ))}
          </div>

          {/* Load More */}
          {hasMore && (
            <div style={{ textAlign: 'center', paddingBottom: 16 }}>
              <button
                className="btn btn-secondary"
                onClick={handleLoadMore}
                disabled={loadingMore}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 8, minWidth: 160 }}
              >
                {loadingMore
                  ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Loading…</>
                  : `Load More (${total - services.length} remaining)`
                }
              </button>
            </div>
          )}
        </>
      )}

      {/* Service Detail Modal */}
      <ServiceDetailModal service={selectedService} onClose={() => setSelected(null)} />
    </div>
  )
}
