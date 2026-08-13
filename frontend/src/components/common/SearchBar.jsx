import { Search, X } from 'lucide-react'

export default function SearchBar({ value, onChange, onClear, placeholder = 'Search...' }) {
  return (
    <div style={{ position: 'relative', flex: 1, minWidth: 240 }}>
      <Search size={16} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
      <input
        type="text"
        className="form-input"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{ paddingLeft: 40, paddingRight: value ? 36 : 14, height: 42, fontSize: 14 }}
      />
      {value && (
        <button
          type="button"
          onClick={onClear}
          style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', border: 'none', background: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
        >
          <X size={14} />
        </button>
      )}
    </div>
  )
}
