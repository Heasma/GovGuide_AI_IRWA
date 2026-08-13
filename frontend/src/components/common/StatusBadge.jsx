export default function StatusBadge({ status }) {
  const normalized = (status || '').toLowerCase()

  let style = { background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1' }

  if (normalized.includes('completed') || normalized.includes('active') || normalized.includes('verified') || normalized.includes('success') || normalized.includes('digital') || normalized.includes('online')) {
    style = { background: '#ecfdf5', color: '#047857', border: '1px solid #a7f3d0' }
  } else if (normalized.includes('pending') || normalized.includes('processing') || normalized.includes('appointment')) {
    style = { background: '#fffbeb', color: '#b45309', border: '1px solid #fde68a' }
  } else if (normalized.includes('error') || normalized.includes('failed') || normalized.includes('inactive')) {
    style = { background: '#fef2f2', color: '#b91c1c', border: '1px solid #fecaca' }
  }

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: '3px 10px',
      borderRadius: '9999px',
      fontSize: 11,
      fontWeight: 600,
      textTransform: 'capitalize',
      letterSpacing: '0.02em',
      ...style
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor' }} />
      {status}
    </span>
  )
}
