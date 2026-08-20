/**
 * GovGuide AI — Dashboard Page
 *
 * Fully database-driven. All metrics, categories, recent activity,
 * and system status badges are retrieved live from backend APIs.
 * Zero hardcoded mock stats or fabricated Sri Lankan datasets.
 */

import { useState, useEffect } from 'react'
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
  Clock,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  RefreshCw,
  Layers,
} from 'lucide-react'
import PageHeader from '../components/common/PageHeader'
import StatCard from '../components/common/StatCard'
import ChartCard from '../components/common/ChartCard'
import { governmentService } from '../services/governmentService'
import { sessionService } from '../services/sessionService'

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const name = user?.email?.split('@')[0] || 'Citizen'

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Real KPI states
  const [servicesCount, setServicesCount] = useState(0)
  const [officesCount, setOfficesCount] = useState(0)
  const [sourcesCount, setSourcesCount] = useState(0)
  const [healthStatus, setHealthStatus] = useState(null)

  // Real Chart Data
  const [categoryChartData, setCategoryChartData] = useState([])
  const [statusChartData, setStatusChartData] = useState([])

  // Real Recent Activity from sessions
  const [recentSessions, setRecentSessions] = useState([])

  const loadDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      // 1. Fetch services to get total count & distribution
      const servicesRes = await governmentService.listServices(0, 100)
      const totalServices = servicesRes?.total || 0
      const items = servicesRes?.items || []
      setServicesCount(totalServices)

      // Count unique offices if present
      const uniqueOffices = new Set()
      items.forEach((item) => {
        if (item.office?.name) uniqueOffices.add(item.office.name)
      })
      setOfficesCount(uniqueOffices.size)

      // Compute category distribution chart from real database records
      const catCounts = {}
      items.forEach((item) => {
        const cat = item.category ? item.category.replace(/_/g, ' ') : 'General'
        catCounts[cat] = (catCounts[cat] || 0) + 1
      })

      const palette = ['#2563eb', '#6366f1', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']
      const catEntries = Object.entries(catCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6)
      const maxCatCount = Math.max(...catEntries.map((e) => e[1]), 1)

      const computedCatChart = catEntries.map(([catName, count], idx) => ({
        label: catName.charAt(0).toUpperCase() + catName.slice(1),
        value: count,
        percentage: Math.round((count / maxCatCount) * 100),
        color: palette[idx % palette.length],
      }))
      setCategoryChartData(computedCatChart)

      // Compute Inspection / Renewal requirement breakdown
      let inspectionNeeded = 0
      let renewalNeeded = 0
      let onlineApply = 0
      items.forEach((item) => {
        if (item.inspection_required) inspectionNeeded++
        if (item.renewal_required) renewalNeeded++
        if (item.application_portal_url && item.application_portal_url !== 'NOT_AVAILABLE') onlineApply++
      })

      const statusBreakdown = [
        { label: 'Online Application Available', value: onlineApply, percentage: Math.round((onlineApply / (totalServices || 1)) * 100), color: '#10b981' },
        { label: 'Renewal Required', value: renewalNeeded, percentage: Math.round((renewalNeeded / (totalServices || 1)) * 100), color: '#6366f1' },
        { label: 'Inspection Required', value: inspectionNeeded, percentage: Math.round((inspectionNeeded / (totalServices || 1)) * 100), color: '#f59e0b' },
      ]
      setStatusChartData(statusBreakdown)

      // 2. Fetch sources count
      try {
        const sourcesRes = await governmentService.listSources(0, 10)
        setSourcesCount(sourcesRes?.total || 0)
      } catch {
        setSourcesCount(0)
      }

      // 3. Fetch real sessions for recent activity
      try {
        const sessionsRes = await sessionService.listSessions()
        setRecentSessions(sessionsRes || [])
      } catch {
        setRecentSessions([])
      }

      // 4. Fetch system health
      try {
        const health = await governmentService.getHealth()
        setHealthStatus(health)
      } catch {
        setHealthStatus({ status: 'degraded', database: 'unavailable' })
      }
    } catch (err) {
      setError('Unable to load dashboard data. Please check connection.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <PageHeader
          title={`Welcome back, ${name} 👋`}
          subtitle="GovGuide AI — Public municipal service discovery & agentic intelligence system."
          badgeText={healthStatus?.database === 'ok' ? 'Live Database Connected' : 'Checking Database'}
        />
        <button
          className="btn btn-secondary btn-sm"
          onClick={loadDashboardData}
          title="Refresh metrics"
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 4 }}
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--color-text-muted)' }}>
          <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 16px', display: 'block' }} />
          <p style={{ fontSize: 14 }}>Connecting to PostgreSQL & synchronizing registry metrics...</p>
        </div>
      )}

      {!loading && error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '14px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, fontSize: 13, color: '#991b1b', marginBottom: 28 }}>
          <AlertTriangle size={16} style={{ flexShrink: 0 }} /> {error}
        </div>
      )}

      {!loading && (
        <>
          {/* KPI Cards Grid */}
          <div className="stat-grid" style={{ marginBottom: 32, gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
            <StatCard
              title="Government Services"
              value={servicesCount}
              icon={Building2}
              color="blue"
              subtext="Active license types in DB"
            />
            <StatCard
              title="Issuing Authorities"
              value={officesCount}
              icon={Landmark}
              color="indigo"
              subtext={officesCount > 0 ? 'Mapped authorities' : 'Unseeded in DB'}
            />
            <StatCard
              title="Knowledge Sources"
              value={sourcesCount}
              icon={Database}
              color="green"
              subtext="Indexed web portals"
            />
            <StatCard
              title="Database Engine"
              value={healthStatus?.database === 'ok' ? 'Online' : 'Degraded'}
              icon={Activity}
              color={healthStatus?.database === 'ok' ? 'green' : 'amber'}
              subtext="PostgreSQL 16"
            />
          </div>

          {/* Analytics Charts Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 24, marginBottom: 32 }}>
            <ChartCard
              title="License Categories Breakdown"
              subtitle="Distribution derived from active government_services rows"
              type="bar"
              data={categoryChartData.length > 0 ? categoryChartData : [{ label: 'No Data', value: 0, percentage: 0, color: '#94a3b8' }]}
            />
            <ChartCard
              title="Service Requirements Breakdown"
              subtitle="Analysis of application, inspection & renewal rules"
              type="horizontal-bar"
              data={statusChartData.length > 0 ? statusChartData : [{ label: 'No Data', value: 0, percentage: 0, color: '#94a3b8' }]}
            />
          </div>

          {/* Quick Access & Recent Activity */}
          <div style={{ display: 'grid', gridTemplateColumns: '7fr 5fr', gap: 24, alignItems: 'start' }}>
            {/* Recent Activity Table */}
            <div className="card premium-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <h2 className="text-h2" style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>
                    Recent AI Consultations
                  </h2>
                  <p className="text-small" style={{ color: 'var(--color-text-secondary)', margin: '2px 0 0' }}>
                    Real user query sessions from database
                  </p>
                </div>
                <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', background: 'var(--color-surface-2)', padding: '4px 8px', borderRadius: 4 }}>
                  Live Session Store
                </span>
              </div>

              {recentSessions.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--color-text-muted)', fontSize: 13 }}>
                  No recent AI dialogue sessions found in database.
                  <div style={{ marginTop: 12 }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => navigate('/chat')}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                    >
                      <Bot size={14} /> Start Consultation
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                        <th style={{ padding: '8px 12px', fontWeight: 600 }}>Session Reference</th>
                        <th style={{ padding: '8px 12px', fontWeight: 600 }}>Started</th>
                        <th style={{ padding: '8px 12px', fontWeight: 600, textAlign: 'right' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recentSessions.slice(0, 5).map((session) => (
                        <tr key={session.session_id} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                          <td style={{ padding: '10px 12px', fontWeight: 600 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                              <Bot size={14} style={{ color: 'var(--color-primary)' }} />
                              <code>{session.session_id.substring(0, 12)}...</code>
                            </div>
                          </td>
                          <td style={{ padding: '10px 12px', color: 'var(--color-text-muted)', fontSize: 12 }}>
                            <Clock size={11} style={{ display: 'inline', marginRight: 4 }} />
                            {session.started_at ? new Date(session.started_at).toLocaleDateString() : 'N/A'}
                          </td>
                          <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                            <button
                              className="btn btn-ghost btn-sm"
                              onClick={() => navigate('/conversations')}
                              style={{ color: 'var(--color-primary)', fontSize: 12 }}
                            >
                              Open →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Quick Shortcuts */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="card premium-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/chat')}>
                <div style={{ color: 'var(--color-accent)', marginBottom: 12 }}>
                  <Bot size={28} />
                </div>
                <h3 className="text-h2" style={{ marginBottom: 6, fontSize: 16, fontWeight: 700 }}>
                  Agentic AI Assistant
                </h3>
                <p className="text-small" style={{ color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: 16 }}>
                  Query the evidence-grounded agent pipeline for public policy inquiries and licensing guidance.
                </p>
                <span className="btn btn-primary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  Launch Assistant <ChevronRight size={14} />
                </span>
              </div>

              <div className="card premium-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/services')}>
                <div style={{ color: 'var(--color-blue)', marginBottom: 12 }}>
                  <Building2 size={28} />
                </div>
                <h3 className="text-h2" style={{ marginBottom: 6, fontSize: 16, fontWeight: 700 }}>
                  Services Catalogue
                </h3>
                <p className="text-small" style={{ color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: 16 }}>
                  Browse all {servicesCount} active City of Chicago business license categories and fee structures.
                </p>
                <span className="btn btn-secondary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  Explore Catalogue <ChevronRight size={14} />
                </span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
