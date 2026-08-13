import { Building2, ChevronRight } from 'lucide-react'
import StatusBadge from './StatusBadge'

export default function ServiceCard({ service, onClick }) {
  return (
    <div className="card premium-card" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-accent)', background: 'rgba(99, 102, 241, 0.1)', padding: '2px 8px', borderRadius: 4 }}>
          {service.category}
        </span>
        <StatusBadge status={service.status} />
      </div>

      <h3 className="text-h2" style={{ fontSize: 16, fontWeight: 700, marginBottom: 8, color: 'var(--color-text-primary)' }}>
        {service.name}
      </h3>

      <p className="text-body" style={{ fontSize: 13, color: 'var(--color-text-secondary)', flex: 1, marginBottom: 16, lineHeight: 1.5 }}>
        {service.description}
      </p>

      <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--color-text-muted)' }}>
          <Building2 size={14} />
          <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 180 }}>{service.department}</span>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={() => onClick(service)} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          View Details <ChevronRight size={12} />
        </button>
      </div>
    </div>
  )
}
