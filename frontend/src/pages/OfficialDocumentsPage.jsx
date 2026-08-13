import { useState } from 'react'
import PageHeader from '../components/common/PageHeader'
import SearchBar from '../components/common/SearchBar'
import StatusBadge from '../components/common/StatusBadge'
import { mockDocuments } from '../data/mockData'
import { FileText, Download, Eye } from 'lucide-react'

export default function OfficialDocumentsPage() {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredDocs = mockDocuments.filter(doc => 
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.type.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader 
        title="Official Documents Registry" 
        subtitle="Indexed government acts, gazettes, departmental circulars, and official procedures."
      />

      <div style={{ marginBottom: 24 }}>
        <SearchBar value={searchTerm} onChange={setSearchTerm} onClear={() => setSearchTerm('')} placeholder="Search official documents by title, department, or circular number..." />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20 }}>
        {filteredDocs.map(doc => (
          <div key={doc.id} className="card premium-card" style={{ display: 'flex', flexDirection: 'column', padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: '#475569', background: '#f1f5f9', padding: '2px 8px', borderRadius: 4 }}>
                {doc.type}
              </span>
              <StatusBadge status={doc.verificationStatus} />
            </div>

            <h3 className="text-h2" style={{ fontSize: 15, fontWeight: 700, marginBottom: 8, flex: 1, color: 'var(--color-text-primary)' }}>
              {doc.title}
            </h3>

            <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
              <div><strong>Department:</strong> {doc.department}</div>
              <div><strong>Published:</strong> {doc.publishedDate} ({doc.fileSize})</div>
            </div>

            <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 12, display: 'flex', gap: 8 }}>
              <button className="btn btn-secondary btn-sm btn-full" onClick={() => alert(`Demonstration View: ${doc.title}`)}>
                <Eye size={14} /> Preview
              </button>
              <button className="btn btn-primary btn-sm btn-full" onClick={() => alert(`Demonstration Download: ${doc.title}`)}>
                <Download size={14} /> Download
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
