import { AlertCircle } from 'lucide-react'

export default function PageHeader({ title, subtitle, badgeText = "Demonstration Data", showDemoNotice = true }) {
  return (
    <div className="page-header" style={{ marginBottom: 28 }}>
      {showDemoNotice && (
        <div className="demo-banner" style={{ marginBottom: 16 }}>
          <AlertCircle size={15} style={{ flexShrink: 0 }} />
          <span>
            <strong>Academic Project Notice</strong> — {badgeText}. Government dataset integration is pending; displayed content uses structured demonstration entries.
          </span>
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 className="text-display" style={{ fontSize: 26, fontWeight: 700, marginBottom: 4, letterSpacing: '-0.02em' }}>
            {title}
          </h1>
          {subtitle && (
            <p className="text-body" style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
              {subtitle}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
