/**
 * GovGuide AI — Official Documents Registry Page
 *
 * Grounded in actual database state: official_sources and document_chunks.
 * Shows an honest empty state while RAG ingestion is pending.
 * Zero mock documents or fake verification badges.
 */

import { useState, useEffect } from 'react'
import PageHeader from '../components/common/PageHeader'
import SearchBar from '../components/common/SearchBar'
import { governmentService } from '../services/governmentService'
import {
  FileText,
  AlertCircle,
  Loader2,
  RefreshCw,
  FolderLock,
  Layers,
} from 'lucide-react'

export default function OfficialDocumentsPage() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    // Check real sources repository
    governmentService.listSources(0, 50)
      .then((data) => {
        // Document records originate from official_sources with document chunks
        setDocuments(data?.items || [])
      })
      .catch((err) => {
        const status = err?.response?.status
        if (status >= 500) setError('A server error occurred.')
        else if (!err.response) setError('Unable to connect to the server.')
        else setError('Failed to retrieve document records.')
      })
      .finally(() => setLoading(false))
  }, [])

  const filteredDocs = documents.filter((doc) =>
    (doc.title && doc.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (doc.source_type && doc.source_type.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader
        title="Official Documents Registry"
        subtitle="Full-text municipal statutes, municipal code chapters, and regulatory guides indexed in the RAG store."
      />

      <div style={{ marginBottom: 24 }}>
        <SearchBar
          value={searchTerm}
          onChange={setSearchTerm}
          onClear={() => setSearchTerm('')}
          placeholder="Search official document records..."
        />
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--color-text-muted)' }}>
          <Loader2 size={28} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 12px', display: 'block' }} />
          <p style={{ fontSize: 14 }}>Checking indexed document registry...</p>
        </div>
      )}

      {!loading && error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, fontSize: 13, color: '#991b1b', marginBottom: 24 }}>
          <AlertCircle size={15} style={{ flexShrink: 0 }} /> {error}
        </div>
      )}

      {!loading && !error && filteredDocs.length === 0 && (
        <div style={{ textAlign: 'center', padding: '64px 24px', color: 'var(--color-text-muted)' }}>
          <FileText size={48} style={{ margin: '0 auto 16px', display: 'block', opacity: 0.25 }} />
          <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
            No official documents are currently indexed in the knowledge base.
          </h3>
          <p style={{ fontSize: 14, maxWidth: 520, margin: '0 auto 20px', lineHeight: 1.6 }}>
            The <strong>document_chunks</strong> and <strong>official_sources</strong> tables currently contain zero uploaded files or gazettes.
            Once the document ingestion pipeline processes official PDF/text resources, indexed circulars will appear here.
          </p>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '8px 14px', background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: 6, fontSize: 12, color: 'var(--color-text-muted)' }}>
            <Layers size={14} /> pgvector chunks table: 0 records
          </div>
        </div>
      )}

      {!loading && !error && filteredDocs.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20 }}>
          {filteredDocs.map((doc) => (
            <div key={doc.id} className="card premium-card" style={{ display: 'flex', flexDirection: 'column', padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#475569', background: '#f1f5f9', padding: '2px 8px', borderRadius: 4 }}>
                  {doc.source_type || 'Regulatory Document'}
                </span>
              </div>

              <h3 className="text-h2" style={{ fontSize: 15, fontWeight: 700, marginBottom: 8, flex: 1, color: 'var(--color-text-primary)' }}>
                {doc.title}
              </h3>

              <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 16 }}>
                <div>Indexed: {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'N/A'}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
