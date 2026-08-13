export default function ChartCard({ title, subtitle, type = 'bar', data = [] }) {
  return (
    <div className="card premium-card" style={{ padding: 20 }}>
      <div style={{ marginBottom: 16 }}>
        <h3 className="text-h2" style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>{title}</h3>
        {subtitle && <p className="text-small" style={{ color: 'var(--color-text-secondary)', margin: '2px 0 0' }}>{subtitle}</p>}
      </div>

      {type === 'bar' && (
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, height: 160, paddingTop: 20 }}>
          {data.map((item, i) => (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%' }}>
              <div style={{ flex: 1, width: '100%', display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
                <div style={{
                  width: '60%',
                  height: `${item.percentage}%`,
                  background: item.color || 'var(--color-primary)',
                  borderRadius: '4px 4px 0 0',
                  transition: 'height 0.3s ease'
                }} title={`${item.label}: ${item.value}`} />
              </div>
              <span className="text-caption" style={{ fontSize: 10, marginTop: 8, color: 'var(--color-text-muted)' }}>{item.label}</span>
            </div>
          ))}
        </div>
      )}

      {type === 'horizontal-bar' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {data.map((item, i) => (
            <div key={i}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4, color: 'var(--color-text-secondary)' }}>
                <span>{item.label}</span>
                <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{item.value}</span>
              </div>
              <div style={{ width: '100%', height: 8, background: 'var(--color-surface-2)', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${item.percentage}%`, height: '100%', background: item.color || 'var(--color-primary)', borderRadius: 4 }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
