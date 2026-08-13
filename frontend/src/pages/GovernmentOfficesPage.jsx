import { useState } from 'react'
import PageHeader from '../components/common/PageHeader'
import SearchBar from '../components/common/SearchBar'
import Modal from '../components/common/Modal'
import { mockOffices } from '../data/mockData'
import { Landmark, MapPin, Phone, Clock, ChevronRight } from 'lucide-react'

export default function GovernmentOfficesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedOffice, setSelectedOffice] = useState(null)

  const filteredOffices = mockOffices.filter(off => 
    off.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    off.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
    off.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
    off.district.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader 
        title="Government Office Directory" 
        subtitle="Locate public department offices, operational hours, contact details, and branch services."
      />

      <div style={{ marginBottom: 28 }}>
        <SearchBar 
          value={searchTerm} 
          onChange={setSearchTerm} 
          onClear={() => setSearchTerm('')} 
          placeholder="Search by office name, district, or location..." 
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20 }}>
        {filteredOffices.map(office => (
          <div key={office.id} className="card premium-card" style={{ display: 'flex', flexDirection: 'column', padding: 20 }}>
            <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', marginBottom: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 8, background: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyCenter: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Landmark size={20} />
              </div>
              <div>
                <h3 className="text-h2" style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>{office.name}</h3>
                <div style={{ fontSize: 12, color: 'var(--color-accent)', fontWeight: 600, marginTop: 2 }}>{office.department}</div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, color: 'var(--color-text-secondary)', margin: '12px 0 16px', flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <MapPin size={14} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
                <span>{office.location}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Phone size={14} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
                <span>{office.contact}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Clock size={14} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
                <span>{office.hours}</span>
              </div>
            </div>

            <button className="btn btn-secondary btn-full" onClick={() => setSelectedOffice(office)}>
              View Office Details <ChevronRight size={14} />
            </button>
          </div>
        ))}
      </div>

      <Modal isOpen={!!selectedOffice} onClose={() => setSelectedOffice(null)} title={selectedOffice?.name || 'Office Details'}>
        {selectedOffice && (
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-accent)', marginBottom: 16 }}>{selectedOffice.department}</div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, background: 'var(--color-surface-2)', padding: 16, borderRadius: 8, marginBottom: 20, fontSize: 13 }}>
              <div><strong>District:</strong> {selectedOffice.district}</div>
              <div><strong>Address:</strong> {selectedOffice.location}</div>
              <div><strong>Telephone:</strong> {selectedOffice.contact}</div>
              <div><strong>Hours:</strong> {selectedOffice.hours}</div>
            </div>

            <h4 className="text-h3" style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>Available Branch Services</h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>
              {selectedOffice.servicesAvailable.map((srv, i) => (
                <span key={i} style={{ fontSize: 12, background: '#e0e7ff', color: '#3730a3', padding: '4px 10px', borderRadius: 4, fontWeight: 500 }}>
                  {srv}
                </span>
              ))}
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
