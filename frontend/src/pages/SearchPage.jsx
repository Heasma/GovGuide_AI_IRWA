import { useState } from 'react'
import { Search, AlertCircle, FileText } from 'lucide-react'
import EmptyState from '../components/common/EmptyState'

// Import assets
import datasetPendingImg from '../assets/illustrations/dataset_pending.svg'

export default function SearchPage() {
  const [query, setQuery] = useState('')

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1000, margin: '0 auto' }} className="fade-in">
      {/* Demo Banner */}
      <div className="demo-banner" style={{ marginBottom: 28 }}>
        <AlertCircle size={16} style={{ marginRight: 8, flexShrink: 0 }} />
        <span>
          <strong>Dataset Notice</strong> — Government service registries will activate here upon final database loading.
        </span>
      </div>

      {/* Hero search */}
      <div className="search-hero" style={{ textAlign: 'center', marginBottom: 40, padding: '32px 0' }}>
        <h2 className="text-display" style={{ marginBottom: 8 }}>Government Service Search</h2>
        <p className="text-body" style={{ color: 'var(--color-text-secondary)', marginBottom: 24, maxWidth: 580, margin: '0 auto 24px' }}>
          Find official government services, eligibility criteria, and application procedures across all public offices.
        </p>
        
        <div className="search-input-wrapper" style={{ maxWidth: 640, margin: '0 auto' }}>
          <div className="form-input-container" style={{ flex: 1 }}>
            <Search size={18} className="form-input-icon" />
            <input
              id="service-search-input"
              type="text"
              className="search-input form-input-with-icon"
              placeholder="Search for a government service (e.g. Passport, Business Permit)..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <button className="btn btn-primary" style={{ flexShrink: 0, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <Search size={16} /> Search
          </button>
        </div>
      </div>

      {/* Reusable Empty State */}
      <EmptyState
        illustration={datasetPendingImg}
        title="Government knowledge base is being prepared"
        description="The official government service dataset has not been integrated into the active database index. Once loaded, this workspace will display searchable, filterable government services with detailed requirements, fees, and eligibility checks."
        action={
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: 'var(--color-text-muted)', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <FileText size={14} /> Mappings: CSV / JSON / XML Registry
            </span>
          </div>
        }
      />
    </div>
  )
}
