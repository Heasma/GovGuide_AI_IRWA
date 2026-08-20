/**
 * GovGuide AI — Government Offices Page
 *
 * The government_offices table currently has 0 records.
 * Displays an honest, professional empty state with actual DB status.
 * If/when offices are seeded, this page will show real records automatically
 * from the nested office data on service responses.
 */

import { useEffect, useState } from 'react'
import PageHeader from '../components/common/PageHeader'
import { Landmark, AlertCircle, RefreshCw, Loader2, MapPin, Phone, Mail, Globe, Clock } from 'lucide-react'
import { governmentService } from '../services/governmentService'
import Modal from '../components/common/Modal'

// Extract unique offices from the services list (office is nested on each service)
function extractOffices(services) {
  const seen = new Set()
  const offices = []
  for (const svc of services) {
    const o = svc.office
    if (!o) continue
    const key = o.id || o.name
    if (key && !seen.has(key)) {
      seen.add(key)
      offices.push(o)
    }
  }
  return offices
}

function OfficeCard({ office, onClick }) {
  return (
    <div className="card premium-card" style={{ display: 'flex', flexDirection: 'column', padding: 20 }}>
      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', marginBottom: 12 }}>
        <div style={{ width: 40, height: 40, borderRadius: 8, background: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Landmark size={20} />
        </div>
        <div>
          <h3 className="text-h2" style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>{office.name}</h3>
          {office.department && <div style={{ fontSize: 12, color: 'var(--color-accent)', fontWeight: 600, marginTop: 2 }}>{office.department}</div>}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 7, fontSize: 13, color: 'var(--color-text-secondary)', flex: 1, marginBottom: 14 }}>
        {(office.street_address || office.city) && (
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 7 }}>
            <MapPin size={13} style={{ color: 'var(--color-text-muted)', flexShrink: 0, marginTop: 1 }} />
            <span>{[office.street_address, office.city, office.state, office.zip_code].filter(Boolean).join(', ')}</span>
          </div>
        )}
        {office.phone && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <Phone size={13} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
            <span>{office.phone}</span>
          </div>
        )}
        {office.email && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <Mail size={13} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
            <span>{office.email}</span>
          </div>
        )}
        {office.business_hours && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <Clock size={13} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
            <span>{office.business_hours}</span>
          </div>
        )}
      </div>

      <button className="btn btn-secondary btn-sm btn-full" onClick={() => onClick(office)}
        style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 5 }}>
        View Office Details
      </button>
    </div>
  )
}

function OfficeDetailModal({ office, onClose }) {
  if (!office) return null
  return (
    <Modal isOpen={!!office} onClose={onClose} title={office.name}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13 }}>
        {office.department && <div><strong>Department:</strong> {office.department}</div>}
        {(office.street_address || office.city) && (
          <div><strong>Address:</strong> {[office.street_address, office.city, office.state, office.zip_code].filter(Boolean).join(', ')}</div>
        )}
        {office.phone && <div><strong>Phone:</strong> {office.phone}</div>}
        {office.email && <div><strong>Email:</strong> {office.email}</div>}
        {office.business_hours && <div><strong>Business Hours:</strong> {office.business_hours}</div>}
        {office.website_url && (
          <div>
            <strong>Website:</strong>{' '}
            <a href={office.website_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              {office.website_url} <Globe size={12} />
            </a>
          </div>
        )}
      </div>
    </Modal>
  )
}

export default function GovernmentOfficesPage() {
  const [offices, setOffices]     = useState([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)
  const [selected, setSelected]   = useState(null)

  useEffect(() => {
    // Attempt to extract offices from the service records' nested `office` field
    governmentService.listServices(0, 100)
      .then(res => {
        const extracted = extractOffices(res.items || [])
        setOffices(extracted)
      })
      .catch(err => {
        const status = err?.response?.status
        if (status >= 500) setError('A server error occurred. Please try again.')
        else if (!err.response) setError('Unable to connect. Please check your connection.')
        else setError('Failed to load office data.')
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader
        title="Government Office Directory"
        subtitle="City of Chicago business licensing office locations, contact information, and operating hours."
      />

      {loading && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--color-text-muted)' }}>
          <Loader2 size={28} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 12px', display: 'block' }} />
          <p style={{ fontSize: 14 }}>Loading office directory…</p>
        </div>
      )}

      {!loading && error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, fontSize: 13, color: '#991b1b' }}>
          <AlertCircle size={15} style={{ flexShrink: 0 }} /> {error}
          <button className="btn btn-ghost btn-sm" onClick={() => window.location.reload()} style={{ marginLeft: 'auto', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
            <RefreshCw size={13} /> Retry
          </button>
        </div>
      )}

      {!loading && !error && offices.length === 0 && (
        <div style={{ textAlign: 'center', padding: '64px 24px', color: 'var(--color-text-muted)' }}>
          <Landmark size={48} style={{ margin: '0 auto 20px', display: 'block', opacity: 0.2 }} />
          <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
            No government office records are currently available in the database.
          </h3>
          <p style={{ fontSize: 14, maxWidth: 480, margin: '0 auto', lineHeight: 1.6 }}>
            The <strong>government_offices</strong> table has not been seeded yet.
            Office information will appear here automatically once records are added to the database.
          </p>
          <div style={{ marginTop: 20, padding: '10px 16px', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 8, fontSize: 13, color: '#1e40af', display: 'inline-block' }}>
            Issuing authority details are available on individual service records.
          </div>
        </div>
      )}

      {!loading && !error && offices.length > 0 && (
        <>
          <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 20 }}>
            {offices.length} office{offices.length !== 1 ? 's' : ''} found across service records
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20 }}>
            {offices.map((office, i) => (
              <OfficeCard key={office.id || i} office={office} onClick={setSelected} />
            ))}
          </div>
        </>
      )}

      <OfficeDetailModal office={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
