import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { authService } from '../../services/authService'
import { 
  LayoutDashboard, 
  Bot, 
  Search, 
  Building2, 
  Landmark,
  Database,
  FileText,
  BadgeCheck,
  MessageSquare,
  History,
  DatabaseZap,
  Activity,
  LogOut
} from 'lucide-react'

// Import assets
import logoFull from '../../assets/images/logo_full.svg'
import logoMark from '../../assets/images/logo_mark.svg'

const NAVIGATION_SECTIONS = [
  {
    title: "WORKSPACE",
    items: [
      { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/chat', icon: Bot, label: 'AI Assistant' },
      { to: '/search', icon: Search, label: 'Service Search' },
      { to: '/services', icon: Building2, label: 'Government Services' },
      { to: '/offices', icon: Landmark, label: 'Government Offices' },
    ]
  },
  {
    title: "KNOWLEDGE",
    items: [
      { to: '/sources', icon: Database, label: 'Knowledge Sources' },
      { to: '/documents', icon: FileText, label: 'Official Documents' },
      { to: '/verified', icon: BadgeCheck, label: 'Verified Sources' },
    ]
  },
  {
    title: "ACTIVITY",
    items: [
      { to: '/conversations', icon: MessageSquare, label: 'Conversations' },
      { to: '/history', icon: History, label: 'Search History' },
    ]
  },
  {
    title: "SYSTEM",
    items: [
      { to: '/dataset', icon: DatabaseZap, label: 'Dataset Status', badge: 'Pending', badgeColor: '#f59e0b' },
      { to: '/pipeline', icon: Activity, label: 'Pipeline Status', badge: 'Active', badgeColor: '#10b981' },
    ]
  }
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await authService.logout()
    logout()
    navigate('/login')
  }

  const initials = user?.email ? user.email[0].toUpperCase() : 'U'

  return (
    <aside className="sidebar" style={{ background: '#0F172A' }}>
      {/* Logo */}
      <div className="sidebar-logo" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', padding: '24px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <img src={logoMark} alt="Logo" style={{ height: 32 }} />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: '#ffffff' }}>GovGuide AI</span>
            <span style={{ fontSize: 9, fontWeight: 600, color: 'var(--color-text-muted)', letterSpacing: '0.06em' }}>ACADEMIC SYSTEM</span>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAVIGATION_SECTIONS.map((section) => (
          <div key={section.title} className="nav-section" style={{ marginBottom: 20 }}>
            <div className="nav-section-label">{section.title}</div>
            {section.items.map(item => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                  style={({ isActive }) => ({
                    color: isActive ? '#ffffff' : '#94a3b8',
                    background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 12,
                    padding: '10px 16px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 14,
                    fontWeight: 500,
                    transition: 'background 0.15s ease, color 0.15s ease',
                    textDecoration: 'none'
                  })}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <Icon size={16} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span style={{ fontSize: 10, fontWeight: 700, color: item.badgeColor, background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: 4 }}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              )
            })}
          </div>
        ))}
      </nav>

      {/* User footer */}
      <div className="sidebar-footer" style={{ borderTop: '1px solid rgba(255,255,255,0.06)', padding: 16 }}>
        <div className="user-chip" onClick={handleLogout} title="Click to sign out" style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 10,
          background: 'rgba(255, 255, 255, 0.04)',
          padding: '10px 12px',
          borderRadius: 'var(--radius-sm)',
          cursor: 'pointer',
          transition: 'background var(--transition)'
        }}>
          <div className="user-avatar" style={{ 
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
            flexShrink: 0
          }}>{initials}</div>
          <div className="user-info" style={{ flex: 1, minWidth: 0 }}>
            <div className="user-email" style={{ 
              fontSize: 12, 
              fontWeight: 500, 
              color: '#ffffff', 
              whiteSpace: 'nowrap', 
              overflow: 'hidden', 
              textOverflow: 'ellipsis' 
            }}>{user?.email || 'demo@gmail.com'}</div>
            <div className="user-role" style={{ 
              fontSize: 10, 
              color: '#94a3b8', 
              display: 'flex', 
              alignItems: 'center', 
              gap: 4 
            }}>
              <LogOut size={10} /> <span>Sign out</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}
