import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/authService'
import { Search, Bot, ShieldCheck, Mail, Lock, Eye, EyeOff, AlertCircle } from 'lucide-react'

// Import assets
import logoFull from '../assets/images/logo_full.svg'
import logoMark from '../assets/images/logo_mark.svg'
import loginHero from '../assets/illustrations/login_hero.png'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'register') {
        await authService.register(email, password)
        setMode('login')
        setError('')
        alert('Account created! Please sign in.')
      } else {
        await login(email, password)
        navigate('/dashboard')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page fade-in">
      {/* Left panel — Hero & Features */}
      <div className="auth-left">
        <div className="auth-brand">
          <img src={logoFull} alt="GovGuide AI" style={{ height: 52, marginBottom: 16 }} />
          
          <h1 className="auth-hero-title">Government services, simplified by AI.</h1>
          <p className="auth-hero-desc">
            Discover government services, understand eligibility, and get evidence-grounded guidance through intelligent retrieval.
          </p>

          <img 
            src={loginHero} 
            alt="GovGuide AI digital government service portal" 
            className="auth-hero-visual"
            loading="eager"
          />

          <div className="feature-cards-grid">
            <div className="feature-premium-card">
              <div className="feature-premium-icon">
                <Search size={20} />
              </div>
              <div>
                <h3 className="feature-premium-title">Intelligent Retrieval</h3>
                <p className="feature-premium-desc">Hybrid lexical and semantic search across trusted sources.</p>
              </div>
            </div>

            <div className="feature-premium-card">
              <div className="feature-premium-icon">
                <Bot size={20} />
              </div>
              <div>
                <h3 className="feature-premium-title">Multi-Agent Research</h3>
                <p className="feature-premium-desc">Research and advisory agents work together to analyze information.</p>
              </div>
            </div>

            <div className="feature-premium-card">
              <div className="feature-premium-icon">
                <ShieldCheck size={20} />
              </div>
              <div>
                <h3 className="feature-premium-title">Evidence-Grounded</h3>
                <p className="feature-premium-desc">Answers are grounded in retrieved evidence and sources.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right panel — Form */}
      <div className="auth-right">
        <div className="auth-form-box">
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
            <img src={logoMark} alt="Logo Mark" style={{ height: 40 }} />
          </div>

          <div className="auth-form-title text-h1" style={{ textAlign: 'center', marginBottom: 8 }}>
            {mode === 'login' ? 'Welcome back' : 'Create account'}
          </div>
          <div className="auth-form-subtitle text-body" style={{ textAlign: 'center', color: 'var(--color-text-secondary)', marginBottom: 28 }}>
            {mode === 'login'
              ? 'Sign in to your GovGuide AI account'
              : 'Join GovGuide AI to get started'}
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label text-caption" style={{ marginBottom: 8, display: 'block' }}>Email address</label>
              <div className="form-input-container">
                <Mail size={16} className="form-input-icon" />
                <input
                  id="email"
                  type="email"
                  className="form-input form-input-with-icon"
                  placeholder="you@example.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label text-caption" style={{ marginBottom: 8, display: 'block' }}>Password</label>
              <div className="form-input-container">
                <Lock size={16} className="form-input-icon" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  className="form-input form-input-with-icon"
                  placeholder={mode === 'register' ? 'Minimum 8 characters' : '••••••••'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  minLength={8}
                  autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                  disabled={loading}
                />
                <button
                  type="button"
                  className="form-input-toggle"
                  onClick={() => setShowPassword(prev => !prev)}
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="error-state text-small" style={{ marginTop: 16 }}>
                <AlertCircle size={14} style={{ marginRight: 6, flexShrink: 0 }} />
                <span>{error}</span>
              </div>
            )}

            <button
              id="auth-submit-btn"
              type="submit"
              className={`btn btn-primary btn-full btn-lg ${loading ? 'btn-loading' : ''}`}
              disabled={loading}
              style={{ marginTop: 26, height: 48 }}
            >
              {loading ? (
                <span className="loading-dots" style={{ margin: '0 auto' }}>
                  <span className="loading-dot" />
                  <span className="loading-dot" />
                  <span className="loading-dot" />
                </span>
              ) : (
                mode === 'login' ? 'Sign in' : 'Create account'
              )}
            </button>
          </form>

          <div className="auth-switch text-body" style={{ marginTop: 22, textAlign: 'center', color: 'var(--color-text-secondary)' }}>
            {mode === 'login' ? (
              <>Don&apos;t have an account? <a onClick={() => { setMode('register'); setError('') }} style={{ color: 'var(--color-accent)', fontWeight: 600, cursor: 'pointer' }}>Sign up</a></>
            ) : (
              <>Already have an account? <a onClick={() => { setMode('login'); setError('') }} style={{ color: 'var(--color-accent)', fontWeight: 600, cursor: 'pointer' }}>Sign in</a></>
            )}
          </div>

          {/* Demo Account Badge */}
          <div className="academic-card" style={{ position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span className="academic-badge" style={{ display: 'inline-block' }}>Demo Account</span>
              <button 
                type="button" 
                onClick={() => { setEmail('demo@gmail.com'); setPassword('password'); }}
                style={{ 
                  background: 'none', border: 'none', color: 'var(--color-accent)', 
                  fontSize: 12, fontWeight: 600, cursor: 'pointer', padding: 0 
                }}
              >
                Use demo account
              </button>
            </div>
            <p className="academic-text" style={{ margin: 0, fontSize: 13 }}>
              Email: <strong>demo@gmail.com</strong><br/>
              Password: <strong>password</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
