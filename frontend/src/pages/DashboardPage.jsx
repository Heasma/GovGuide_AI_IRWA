import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { 
  Building2, 
  Landmark, 
  Database, 
  FileText, 
  Bot, 
  Search, 
  ChevronRight, 
  Clock 
} from 'lucide-react'
import PageHeader from '../components/common/PageHeader'
import StatCard from '../components/common/StatCard'
import ChartCard from '../components/common/ChartCard'
import StatusBadge from '../components/common/StatusBadge'
import { mockDashboardStats } from '../data/mockData'

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const name = user?.email?.split('@')[0] || 'User'

  const categoryChartData = [
    { label: 'Citizen', value: 45, percentage: 80, color: 'var(--color-primary)' },
    { label: 'Business', value: 28, percentage: 55, color: 'var(--color-accent)' },
    { label: 'Transport', value: 22, percentage: 40, color: '#3b82f6' },
    { label: 'Tax', value: 18, percentage: 32, color: '#10b981' },
    { label: 'Education', value: 15, percentage: 25, color: '#f59e0b' }
  ]

  const deptChartData = [
    { label: 'Immigration & Emigration', value: 14, percentage: 85, color: '#2563eb' },
    { label: 'Motor Traffic Department', value: 22, percentage: 95, color: '#6366f1' },
    { label: 'Inland Revenue Dept', value: 19, percentage: 70, color: '#10b981' },
    { label: 'Registrar General Dept', value: 16, percentage: 60, color: '#f59e0b' }
  ]

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader 
        title={`Welcome back, ${name} 👋`}
        subtitle="GovGuide AI — Information Retrieval and Web Analytics discovery portal."
        badgeText="Demonstration Data Active"
      />

      {/* KPI Cards Grid */}
      <div className="stat-grid" style={{ marginBottom: 32, gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
        <StatCard title="Government Services" value={mockDashboardStats.servicesCount} icon={Building2} color="blue" subtext="Demonstration entries" />
        <StatCard title="Government Offices" value={mockDashboardStats.officesCount} icon={Landmark} color="indigo" subtext="Mapped locations" />
        <StatCard title="Knowledge Sources" value={mockDashboardStats.knowledgeSourcesCount} icon={Database} color="green" subtext="Official portals" />
        <StatCard title="Official Documents" value={mockDashboardStats.documentsCount} icon={FileText} color="amber" subtext="Indexed gazettes" />
      </div>

      {/* Analytics Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 24, marginBottom: 32 }}>
        <ChartCard title="Services by Category" subtitle="Distribution across major government domains" type="bar" data={categoryChartData} />
        <ChartCard title="Services by Department" subtitle="Service count breakdown by leading agencies" type="horizontal-bar" data={deptChartData} />
      </div>

      {/* Quick Access & Recent Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: '7fr 5fr', gap: 24, alignItems: 'start' }}>
        
        {/* Recent Activity Table */}
        <div className="card premium-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <div>
              <h2 className="text-h2" style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Recent System Activity</h2>
              <p className="text-small" style={{ color: 'var(--color-text-secondary)', margin: '2px 0 0' }}>Demonstration audit trail</p>
            </div>
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', background: 'var(--color-surface-2)', padding: '4px 8px', borderRadius: 4 }}>
              Live Log
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                  <th style={{ padding: '8px 12px', fontWeight: 600 }}>Type</th>
                  <th style={{ padding: '8px 12px', fontWeight: 600 }}>Item</th>
                  <th style={{ padding: '8px 12px', fontWeight: 600 }}>Time</th>
                  <th style={{ padding: '8px 12px', fontWeight: 600 }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {mockDashboardStats.recentActivity.map((act) => (
                  <tr key={act.id} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 600 }}>{act.type}</td>
                    <td style={{ padding: '10px 12px', color: 'var(--color-text-secondary)' }}>{act.item}</td>
                    <td style={{ padding: '10px 12px', color: 'var(--color-text-muted)', fontSize: 12 }}>
                      <Clock size={12} style={{ display: 'inline', marginRight: 4 }} />
                      {act.time}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <StatusBadge status={act.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Quick Shortcuts */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card premium-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/chat')}>
            <div style={{ color: 'var(--color-accent)', marginBottom: 12 }}>
              <Bot size={28} />
            </div>
            <h3 className="text-h2" style={{ marginBottom: 6, fontSize: 16, fontWeight: 700 }}>AI Research Assistant</h3>
            <p className="text-small" style={{ color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: 16 }}>
              Query the evidence-grounded agent pipeline for public policy inquiries and eligibility guidance.
            </p>
            <span className="btn btn-primary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              Launch Assistant <ChevronRight size={14} />
            </span>
          </div>

          <div className="card premium-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/search')}>
            <div style={{ color: 'var(--color-blue)', marginBottom: 12 }}>
              <Search size={28} />
            </div>
            <h3 className="text-h2" style={{ marginBottom: 6, fontSize: 16, fontWeight: 700 }}>Service Search</h3>
            <p className="text-small" style={{ color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: 16 }}>
              Locate government services, requirements, and downloadable circulars across all departments.
            </p>
            <span className="btn btn-secondary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              Search Catalogue <ChevronRight size={14} />
            </span>
          </div>
        </div>

      </div>
    </div>
  )
}
