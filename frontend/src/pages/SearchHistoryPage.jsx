import { useState } from 'react'
import PageHeader from '../components/common/PageHeader'
import SearchBar from '../components/common/SearchBar'
import StatusBadge from '../components/common/StatusBadge'
import { mockSearchHistory } from '../data/mockData'
import { History, Search, Trash2, RotateCcw } from 'lucide-react'

export default function SearchHistoryPage() {
  const [history, setHistory] = useState(mockSearchHistory)
  const [searchTerm, setSearchTerm] = useState('')

  const filteredHistory = history.filter(item => 
    item.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.category.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleDelete = (id) => {
    setHistory(prev => prev.filter(i => i.id !== id))
  }

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader 
        title="Search History Audit" 
        subtitle="Recent search queries, retrieved result counts, and category filters."
      />

      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', gap: 16 }}>
        <SearchBar value={searchTerm} onChange={setSearchTerm} onClear={() => setSearchTerm('')} placeholder="Search history entries..." />
        {history.length > 0 && (
          <button className="btn btn-secondary btn-sm" onClick={() => setHistory([])} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--color-danger)' }}>
            <Trash2 size={14} /> Clear All History
          </button>
        )}
      </div>

      <div className="card premium-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: 'var(--color-surface-2)', borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Query</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Category</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Results</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Timestamp</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.map(item => (
                <tr key={item.id} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 600 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Search size={14} style={{ color: 'var(--color-text-muted)' }} />
                      <span>{item.query}</span>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)' }}>{item.category}</td>
                  <td style={{ padding: '14px 16px', fontWeight: 600 }}>{item.resultCount} items</td>
                  <td style={{ padding: '14px 16px', color: 'var(--color-text-muted)' }}>{item.timestamp}</td>
                  <td style={{ padding: '14px 16px' }}><StatusBadge status={item.status} /></td>
                  <td style={{ padding: '14px 16px' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleDelete(item.id)} title="Delete entry" style={{ color: 'var(--color-danger)' }}>
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {filteredHistory.length === 0 && (
        <div style={{ textAlign: 'center', padding: 48, color: 'var(--color-text-muted)' }}>
          No search history entries found.
        </div>
      )}
    </div>
  )
}
