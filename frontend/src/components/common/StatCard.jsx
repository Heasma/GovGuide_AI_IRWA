export default function StatCard({ title, value, icon: Icon, color = 'blue', subtext }) {
  const colorMap = {
    blue: { bg: '#eff6ff', text: '#2563eb' },
    green: { bg: '#ecfdf5', text: '#10b981' },
    amber: { bg: '#fffbeb', text: '#f59e0b' },
    indigo: { bg: '#eef2ff', text: '#6366f1' },
    purple: { bg: '#f3e8ff', text: '#9333ea' }
  }

  const activeColor = colorMap[color] || colorMap.blue

  return (
    <div className="stat-card premium-card" style={{ padding: 20 }}>
      <div className="stat-icon" style={{ background: activeColor.bg, color: activeColor.text }}>
        {Icon && <Icon size={20} />}
      </div>
      <div>
        <div className="stat-value" style={{ fontSize: 22, fontWeight: 700, lineHeight: 1.2 }}>{value}</div>
        <div className="stat-label" style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 2 }}>{title}</div>
        {subtext && <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>{subtext}</div>}
      </div>
    </div>
  )
}
