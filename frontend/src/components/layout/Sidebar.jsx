/**
 * GovGuide AI — Streamlined Citizen-Facing Sidebar
 *
 * Clean, compact, and uncluttered navigation architecture.
 * Groups Knowledge Sources, Official Documents, and Verified Sources under "Knowledge Base".
 * Preserves all routes, authentication, active highlighting, and user session management.
 */

import { useState, useEffect } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { authService } from '../../services/authService'
import {
  LayoutDashboard,
  Bot,
  Search,
  Building2,
  Landmark,
  BookOpen,
  Database,
  FileText,
  BadgeCheck,
  MessageSquare,
  DatabaseZap,
  Activity,
  Briefcase,
  LogOut,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'

import logoMark from '../../assets/images/logo_mark.svg'

const KNOWLEDGE_SUB_ITEMS = [
  { to: '/sources', icon: Database, label: 'Knowledge Sources' },
  { to: '/documents', icon: FileText, label: 'Official Documents' },
  { to: '/verified', icon: BadgeCheck, label: 'Verified Sources' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Auto-expand Knowledge Base when active on one of its child routes
  const isKnowledgeActive = ['/sources', '/documents', '/verified', '/knowledge-sources', '/official-documents', '/verified-sources'].some(
    path => location.pathname === path || location.pathname.startsWith(path + '/')
  )

  const [knowledgeOpen, setKnowledgeOpen] = useState(isKnowledgeActive)

  // Keep open if user navigates to a knowledge sub-route
  useEffect(() => {
    if (isKnowledgeActive) {
      setKnowledgeOpen(true)
    }
  }, [isKnowledgeActive])

  const handleLogout = async () => {
    await authService.logout()
    logout()
    navigate('/login')
  }

  const initials = user?.email ? user.email[0].toUpperCase() : 'U'

  return (
    <aside className="sidebar" style={{ background: '#0F172A' }}>
      {/* Logo Header */}
      <div className="sidebar-logo" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', padding: '20px 20px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <img src={logoMark} alt="Logo" style={{ height: 32 }} />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: '#ffffff' }}>GovGuide AI</span>
            <span style={{ fontSize: 9, fontWeight: 600, color: 'var(--color-text-muted)', letterSpacing: '0.06em' }}>CITIZEN PORTAL</span>
          </div>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="sidebar-nav">
        
        {/* ── WORKSPACE ─────────────────────────────────────── */}
        <div className="nav-section" style={{ marginBottom: 20 }}>
          <div className="nav-section-label">WORKSPACE</div>

          <NavLink
            to="/dashboard"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            style={({ isActive }) => ({
              color: isActive ? '#ffffff' : '#94a3b8',
              background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '9px 16px',
              margin: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: 14,
              fontWeight: 500,
              textDecoration: 'none',
              transition: 'background 0.15s ease, color 0.15s ease',
            })}
          >
            <LayoutDashboard size={16} />
            <span>Dashboard</span>
          </NavLink>

          <NavLink
            to="/chat"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            style={({ isActive }) => ({
              color: isActive ? '#ffffff' : '#94a3b8',
              background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '9px 16px',
              margin: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: 14,
              fontWeight: 500,
              textDecoration: 'none',
              transition: 'background 0.15s ease, color 0.15s ease',
            })}
          >
            <Bot size={16} />
            <span>AI Assistant</span>
          </NavLink>

          <NavLink
            to="/services"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            style={({ isActive }) => ({
              color: isActive ? '#ffffff' : '#94a3b8',
              background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '9px 16px',
              margin: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: 14,
              fontWeight: 500,
              textDecoration: 'none',
              transition: 'background 0.15s ease, color 0.15s ease',
            })}
          >
            <Building2 size={16} />
            <span>Services</span>
          </NavLink>

          <NavLink
            to="/search"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            style={({ isActive }) => ({
              color: isActive ? '#ffffff' : '#94a3b8',
              background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '9px 16px',
              margin: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: 14,
              fontWeight: 500,
              textDecoration: 'none',
              transition: 'background 0.15s ease, color 0.15s ease',
            })}
          >
            <Search size={16} />
            <span>Search</span>
          </NavLink>
        </div>

        {/* ── KNOWLEDGE ─────────────────────────────────────── */}
        <div className="nav-section" style={{ marginBottom: 20 }}>
          <div className="nav-section-label">KNOWLEDGE</div>

          {/* Grouped Knowledge Base Collapsible */}
          <div>
            <button
              type="button"
              onClick={() => setKnowledgeOpen(prev => !prev)}
              className={`nav-item${isKnowledgeActive ? ' active' : ''}`}
              style={{
                width: 'calc(100% - 16px)',
                color: isKnowledgeActive ? '#ffffff' : '#94a3b8',
                background: isKnowledgeActive ? 'rgba(255,255,255,0.08)' : 'transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '9px 16px',
                margin: '2px 8px',
                borderRadius: 'var(--radius-sm)',
                fontSize: 14,
                fontWeight: 500,
                transition: 'background 0.15s ease, color 0.15s ease',
                cursor: 'pointer',
              }}
              title="Toggle Knowledge Base submenus"
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <BookOpen size={16} />
                <span>Knowledge Base</span>
              </div>
              {knowledgeOpen ? <ChevronDown size={14} style={{ opacity: 0.7 }} /> : <ChevronRight size={14} style={{ opacity: 0.7 }} />}
            </button>

            {/* Sub-items for Knowledge Base */}
            {knowledgeOpen && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2, paddingLeft: 16, marginTop: 2, marginBottom: 4 }}>
                {KNOWLEDGE_SUB_ITEMS.map((sub) => {
                  const SubIcon = sub.icon
                  return (
                    <NavLink
                      key={sub.to}
                      to={sub.to}
                      className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                      style={({ isActive }) => ({
                        color: isActive ? '#ffffff' : '#cbd5e1',
                        background: isActive ? 'rgba(99, 102, 241, 0.16)' : 'rgba(255,255,255,0.02)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: '7px 14px',
                        margin: '1px 8px 1px 0',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 13,
                        fontWeight: isActive ? 600 : 400,
                        textDecoration: 'none',
                        transition: 'background 0.15s ease, color 0.15s ease',
                      })}
                    >
                      <SubIcon size={14} style={{ opacity: 0.85 }} />
                      <span>{sub.label}</span>
                    </NavLink>
                  )
                })}
              </div>
            )}
          </div>

          <NavLink
            to="/offices"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            style={({ isActive }) => ({
              color: isActive ? '#ffffff' : '#94a3b8',
              background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '9px 16px',
              margin: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: 14,
              fontWeight: 500,
              textDecoration: 'none',
              transition: 'background 0.15s ease, color 0.15s ease',
            })}
          >
            <Landmark size={16} />
            <span>Government Offices</span>
          </NavLink>
        </div>

        {/* ── ACTIVITY ──────────────────────────────────────── */}
        <div className="nav-section" style={{ marginBottom: 20 }}>
          <div className="nav-section-label">ACTIVITY</div>

          <NavLink
            to="/conversations"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            style={({ isActive }) => ({
              color: isActive ? '#ffffff' : '#94a3b8',
              background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '9px 16px',
              margin: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: 14,
              fontWeight: 500,
              textDecoration: 'none',
              transition: 'background 0.15s ease, color 0.15s ease',
            })}
          >
            <MessageSquare size={16} />
            <span>Conversations</span>
          </NavLink>
        </div>

        {/* ── SYSTEM ────────────────────────────────────────── */}
        <div className="nav-section" style={{ marginBottom: 20 }}>
          <div className="nav-section-label">SYSTEM</div>

          <NavLink
            to="/dataset"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            style={({ isActive }) => ({
              color: isActive ? '#ffffff' : '#94a3b8',
              background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
              padding: '9px 16px',
              margin: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: 14,
              fontWeight: 500,
              textDecoration: 'none',
              transition: 'background 0.15s ease, color 0.15s ease',
            })}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <DatabaseZap size={16} />
              <span>Dataset Status</span>
            </div>
            <span style={{ fontSize: 10, fontWeight: 700, color: '#10b981', background: 'rgba(16, 185, 129, 0.12)', padding: '2px 6px', borderRadius: 4 }}>
              Active
            </span>
          </NavLink>

          <NavLink
            to="/pipeline"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            style={({ isActive }) => ({
              color: isActive ? '#ffffff' : '#94a3b8',
              background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
              padding: '9px 16px',
              margin: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: 14,
              fontWeight: 500,
              textDecoration: 'none',
              transition: 'background 0.15s ease, color 0.15s ease',
            })}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Activity size={16} />
              <span>Pipeline Status</span>
            </div>
            <span style={{ fontSize: 10, fontWeight: 700, color: '#10b981', background: 'rgba(16, 185, 129, 0.12)', padding: '2px 6px', borderRadius: 4 }}>
              Active
            </span>
          </NavLink>
        </div>

        {/* ── BUSINESS ──────────────────────────────────────── */}
        <div className="nav-section" style={{ marginBottom: 20 }}>
          <div className="nav-section-label">BUSINESS</div>

          <NavLink
            to="/commercialization"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            style={({ isActive }) => ({
              color: isActive ? '#ffffff' : '#94a3b8',
              background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
              padding: '9px 16px',
              margin: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: 14,
              fontWeight: 500,
              textDecoration: 'none',
              transition: 'background 0.15s ease, color 0.15s ease',
            })}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Briefcase size={16} />
              <span>Commercialization</span>
            </div>
            <span style={{ fontSize: 10, fontWeight: 700, color: '#818cf8', background: 'rgba(99, 102, 241, 0.14)', padding: '2px 6px', borderRadius: 4 }}>
              Strategy
            </span>
          </NavLink>
        </div>

      </nav>

      {/* ── BOTTOM USER FOOTER ────────────────────────────── */}
      <div className="sidebar-footer" style={{ borderTop: '1px solid rgba(255,255,255,0.06)', padding: 16 }}>
        <div
          className="user-chip"
          onClick={handleLogout}
          title="Click to sign out"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            background: 'rgba(255, 255, 255, 0.04)',
            padding: '10px 12px',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            transition: 'background var(--transition)',
          }}
        >
          <div
            className="user-avatar"
            style={{
              width: 32,
              height: 32,
              background: 'linear-gradient(135deg, var(--color-accent), var(--color-blue))',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 12,
              fontWeight: 700,
              color: 'white',
              flexShrink: 0,
            }}
          >
            {initials}
          </div>
          <div className="user-info" style={{ flex: 1, minWidth: 0 }}>
            <div
              className="user-email"
              style={{
                fontSize: 12,
                fontWeight: 500,
                color: '#ffffff',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {user?.email || 'demo@gmail.com'}
            </div>
            <div
              className="user-role"
              style={{
                fontSize: 10,
                color: '#94a3b8',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <LogOut size={10} /> <span>Sign out</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}
