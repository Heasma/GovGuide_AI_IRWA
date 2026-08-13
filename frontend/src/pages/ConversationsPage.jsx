import { useState } from 'react'
import PageHeader from '../components/common/PageHeader'
import SearchBar from '../components/common/SearchBar'
import StatusBadge from '../components/common/StatusBadge'
import Modal from '../components/common/Modal'
import { mockConversations } from '../data/mockData'
import { MessageSquare, Clock, Bot, User } from 'lucide-react'

export default function ConversationsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedConv, setSelectedConv] = useState(null)

  const filteredConvs = mockConversations.filter(c => 
    c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.queryTopic.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader 
        title="AI Conversation History" 
        subtitle="Review past AI Assistant research dialogues and generated guidance logs."
      />

      <div style={{ marginBottom: 24 }}>
        <SearchBar value={searchTerm} onChange={setSearchTerm} onClear={() => setSearchTerm('')} placeholder="Search conversation threads..." />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20 }}>
        {filteredConvs.map(conv => (
          <div key={conv.id} className="card premium-card" style={{ display: 'flex', flexDirection: 'column', padding: 20, cursor: 'pointer' }} onClick={() => setSelectedConv(conv)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-accent)', background: 'rgba(99, 102, 241, 0.1)', padding: '2px 8px', borderRadius: 4 }}>
                {conv.queryTopic}
              </span>
              <StatusBadge status={conv.status} />
            </div>

            <h3 className="text-h2" style={{ fontSize: 15, fontWeight: 700, marginBottom: 8, color: 'var(--color-text-primary)' }}>
              {conv.title}
            </h3>

            <p className="text-small" style={{ color: 'var(--color-text-secondary)', flex: 1, marginBottom: 16, lineHeight: 1.5, background: 'var(--color-surface-2)', padding: 10, borderRadius: 6 }}>
              "{conv.lastMessage}"
            </p>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: 'var(--color-text-muted)', borderTop: '1px solid var(--color-border)', paddingTop: 12 }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                <Clock size={12} /> {conv.timestamp}
              </span>
              <span>{conv.messageCount} messages</span>
            </div>
          </div>
        ))}
      </div>

      <Modal isOpen={!!selectedConv} onClose={() => setSelectedConv(null)} title={selectedConv?.title || 'Conversation Detail'}>
        {selectedConv && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#2563eb', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <User size={14} />
              </div>
              <div style={{ background: 'var(--color-surface-2)', padding: 12, borderRadius: 8, fontSize: 13, flex: 1 }}>
                Query regarding {selectedConv.title}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#7c3aed', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Bot size={14} />
              </div>
              <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', padding: 12, borderRadius: 8, fontSize: 13, flex: 1, lineHeight: 1.6 }}>
                {selectedConv.lastMessage}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
