import { useState } from 'react'
import PageHeader from '../components/common/PageHeader'
import SearchBar from '../components/common/SearchBar'
import ServiceCard from '../components/common/ServiceCard'
import Modal from '../components/common/Modal'
import { mockServices } from '../data/mockData'
import { CheckCircle2, FileText, ExternalLink, Clock, DollarSign } from 'lucide-react'

export default function GovernmentServicesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [selectedService, setSelectedService] = useState(null)

  const categories = ['All', 'Citizen Services', 'Business Services', 'Education', 'Healthcare', 'Transport', 'Tax & Revenue', 'Social Services']

  const filteredServices = mockServices.filter(srv => {
    const matchesSearch = srv.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          srv.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          srv.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'All' || srv.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader 
        title="Government Services Catalogue" 
        subtitle="Explore available public services, application procedures, eligibility guidelines, and fees."
      />

      {/* Search & Category Filter */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 28 }}>
        <SearchBar 
          value={searchTerm} 
          onChange={setSearchTerm} 
          onClear={() => setSearchTerm('')} 
          placeholder="Search by service name, department, or keywords..." 
        />

        <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 }}>
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`btn ${selectedCategory === cat ? 'btn-primary' : 'btn-secondary'} btn-sm`}
              style={{ borderRadius: 20, whiteSpace: 'nowrap' }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Services Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
        {filteredServices.map(service => (
          <ServiceCard key={service.id} service={service} onClick={setSelectedService} />
        ))}
      </div>

      {filteredServices.length === 0 && (
        <div style={{ textAlign: 'center', padding: 48, color: 'var(--color-text-muted)' }}>
          No government services found matching your criteria.
        </div>
      )}

      {/* Service Detail Modal */}
      <Modal isOpen={!!selectedService} onClose={() => setSelectedService(null)} title={selectedService?.name || 'Service Details'}>
        {selectedService && (
          <div>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 16 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-accent)', background: 'rgba(99, 102, 241, 0.1)', padding: '4px 10px', borderRadius: 4 }}>
                {selectedService.category}
              </span>
              <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{selectedService.department}</span>
            </div>

            <p className="text-body" style={{ color: 'var(--color-text-secondary)', marginBottom: 20, lineHeight: 1.6 }}>
              {selectedService.description}
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, background: 'var(--color-surface-2)', padding: 16, borderRadius: 8, marginBottom: 20 }}>
              <div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Clock size={12} /> Processing Time
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, marginTop: 2 }}>{selectedService.processingTime}</div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <DollarSign size={12} /> Service Fee
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, marginTop: 2 }}>{selectedService.fee}</div>
              </div>
            </div>

            <h4 className="text-h3" style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>Eligibility Criteria</h4>
            <p className="text-small" style={{ color: 'var(--color-text-secondary)', marginBottom: 16 }}>
              {selectedService.eligibility}
            </p>

            <h4 className="text-h3" style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>Required Documents</h4>
            <ul style={{ paddingLeft: 18, fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 24 }}>
              {selectedService.documentsRequired.map((doc, i) => (
                <li key={i} style={{ marginBottom: 4 }}>{doc}</li>
              ))}
            </ul>

            <a href={selectedService.onlineLink} target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-full" style={{ justifyContent: 'center' }}>
              Visit Official Service Portal <ExternalLink size={14} />
            </a>
          </div>
        )}
      </Modal>
    </div>
  )
}
