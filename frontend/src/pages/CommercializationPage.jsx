/**
 * GovGuide AI — Commercialization & Business Strategy Page
 *
 * Exposes the proposed commercialization framework, tiered pricing model,
 * target customer segments, unit economics, deployment architecture,
 * go-to-market roadmap, Responsible AI differentiation, and business value
 * derived from the multi-agent architecture.
 *
 * Source of Truth: COMMERCIALIZATION.md (SLIIT IT3041)
 * Note: Academic commercialization proposal — not an active billing system.
 */

import {
  Briefcase,
  Users,
  Landmark,
  HeartHandshake,
  CheckCircle2,
  Sparkles,
  ShieldCheck,
  Check,
  Bot,
  Database,
  Zap,
  Scale,
  DollarSign,
  Server,
  Cloud,
  Eye,
  BadgeCheck,
  ArrowRight,
  Info,
  Store,
} from 'lucide-react'

export default function CommercializationPage() {
  return (
    <div className="page-container fade-in" style={{ maxWidth: 1280, margin: '0 auto', paddingBottom: 80 }}>
      {/* ── Page Hero ───────────────────────────────────────────── */}
      <section style={{ marginBottom: 32 }} aria-labelledby="commercialization-hero-heading">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: 'var(--color-accent)',
              background: 'rgba(99, 102, 241, 0.1)',
              padding: '3px 10px',
              borderRadius: 'var(--radius-full)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 5,
            }}
          >
            <Briefcase size={12} /> ACADEMIC COMMERCIALIZATION MODEL
          </span>
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: 'var(--color-text-muted)',
            }}
          >
            SLIIT IT3041 • Information Retrieval & Web Analytics
          </span>
        </div>

        <div style={{ marginBottom: 12 }}>
          <h1
            id="commercialization-hero-heading"
            className="text-display"
            style={{ fontSize: 28, fontWeight: 800, marginBottom: 6, letterSpacing: '-0.02em', color: 'var(--color-text-primary)' }}
          >
            Commercialization Strategy
          </h1>
          <p style={{ fontSize: 16, color: 'var(--color-text-secondary)', margin: 0, fontWeight: 500 }}>
            Turn GovGuide AI into a scalable AI-powered government service discovery and information platform.
          </p>
          <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginTop: 4, marginBottom: 0 }}>
            Proposed market, pricing, deployment, and go-to-market strategy for GovGuide AI.
          </p>
        </div>

        {/* Academic Commercialization Banner */}
        <div
          style={{
            background: 'linear-gradient(90deg, #eff6ff, #f8fafc)',
            border: '1px solid #bfdbfe',
            borderRadius: 'var(--radius-md)',
            padding: '14px 18px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 12,
            marginTop: 16,
          }}
        >
          <Info size={18} style={{ color: '#2563eb', flexShrink: 0, marginTop: 2 }} />
          <div style={{ fontSize: 13, color: '#1e3a8a', lineHeight: 1.5 }}>
            <strong>Academic Commercialization Notice:</strong> All pricing tiers, financial projections, unit economics, and operational milestones represent proposed academic assumptions for commercialization planning and do not represent an active billing system or measured production revenues.
          </div>
        </div>
      </section>

      {/* ── 1. Top Business Model Snapshot ──────────────────────── */}
      <section style={{ marginBottom: 44 }} aria-labelledby="snapshot-heading">
        <h2 id="snapshot-heading" style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>
          Business Model Snapshot
        </h2>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: 16,
          }}
        >
          {/* Card 1 */}
          <div className="card" style={{ padding: 20, borderTop: '3px solid #3b82f6' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
              <div style={{ background: '#eff6ff', color: '#2563eb', width: 34, height: 34, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Users size={18} />
              </div>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Target Market</span>
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
              Citizens & Businesses
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0 }}>
              Entrepreneurs, CPAs, legal expeditors, city agencies & NGOs.
            </p>
          </div>

          {/* Card 2 */}
          <div className="card" style={{ padding: 20, borderTop: '3px solid #6366f1' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
              <div style={{ background: '#eef2ff', color: '#6366f1', width: 34, height: 34, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <DollarSign size={18} />
              </div>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Revenue Streams</span>
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
              Subscription • B2G • API
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0 }}>
              SaaS tiers, municipal licensing, and developer API access.
            </p>
          </div>

          {/* Card 3 */}
          <div className="card" style={{ padding: 20, borderTop: '3px solid #10b981' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
              <div style={{ background: '#f0fdf4', color: '#10b981', width: 34, height: 34, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Cloud size={18} />
              </div>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Deployment</span>
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
              SaaS & Sovereign Cloud
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0 }}>
              Multi-tenant cloud, private government hosting, and REST APIs.
            </p>
          </div>

          {/* Card 4 */}
          <div className="card" style={{ padding: 20, borderTop: '3px solid #f59e0b' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
              <div style={{ background: '#fffbeb', color: '#d97706', width: 34, height: 34, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Zap size={18} />
              </div>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Proposed Pricing</span>
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
              Free • $49/mo • Enterprise
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0 }}>
              Freemium citizen discovery with professional and enterprise tiers.
            </p>
          </div>
        </div>
      </section>

      {/* ── 2. Target Customer Segments ─────────────────────────── */}
      <section style={{ marginBottom: 48 }} aria-labelledby="segments-heading">
        <div style={{ marginBottom: 20 }}>
          <h2 id="segments-heading" style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Target Customer Segments
          </h2>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            Four primary customer segments across citizen discovery, professional licensing advisory, and municipal governance.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 20,
          }}
        >
          {/* Segment 1: Citizens */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Store size={20} />
              </div>
              <div>
                <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                  Citizens & First-Time Entrepreneurs
                </h3>
                <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Founders • Food Truck • Retail Starters</span>
              </div>
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: 16, flex: 1 }}>
              Free, plain-language self-service discovery of permits, filing fees, and municipal procedures to reduce confusion and application delays.
            </p>
            <div style={{ background: 'var(--color-surface-2)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', fontSize: 12, color: 'var(--color-text-secondary)' }}>
              <strong style={{ color: 'var(--color-text-primary)' }}>Key Use Case:</strong> Finding whether a Mobile Food Vendor or Retail Food license is required and identifying zoning prerequisites.
            </div>
          </div>

          {/* Segment 2: CPAs & Expeditors */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: '#eef2ff', color: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Briefcase size={20} />
              </div>
              <div>
                <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                  Professional Consultants & Expeditors
                </h3>
                <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Legal Advisors • CPA Firms • Permit Agents</span>
              </div>
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: 16, flex: 1 }}>
              Multi-client licensing support, eligibility analysis, compliance checklists, and verified citations for client filings.
            </p>
            <div style={{ background: 'var(--color-surface-2)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', fontSize: 12, color: 'var(--color-text-secondary)' }}>
              <strong style={{ color: 'var(--color-text-primary)' }}>Key Use Case:</strong> Generating exportable licensing compliance packages with verifiable municipal citations.
            </div>
          </div>

          {/* Segment 3: Municipal Agencies */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: '#f0fdf4', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Landmark size={20} />
              </div>
              <div>
                <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                  Municipal Agencies & City Governments
                </h3>
                <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>311 Contact Centers • City Clerks • BACP</span>
              </div>
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: 12, flex: 1 }}>
              Proposed white-label AI co-pilot deployment for municipal portals and contact centers.
            </p>
            <div style={{ background: 'var(--color-surface-2)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
              <strong style={{ color: 'var(--color-text-primary)' }}>Key Use Case:</strong> Providing 24/7 grounded citizen guidance through official city websites and contact channels.
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
              * Illustrative target / proposed outcome: Potential support volume reduction.
            </div>
          </div>

          {/* Segment 4: NGOs */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: '#faf5ff', color: '#a855f7', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <HeartHandshake size={20} />
              </div>
              <div>
                <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                  NGOs & Development Organizations
                </h3>
                <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>CDFIs • MWBE Support • Non-Profits</span>
              </div>
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: 16, flex: 1 }}>
              Plain-language access to licensing information for organizations supporting underserved entrepreneurs.
            </p>
            <div style={{ background: 'var(--color-surface-2)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', fontSize: 12, color: 'var(--color-text-secondary)' }}>
              <strong style={{ color: 'var(--color-text-primary)' }}>Key Use Case:</strong> Helping users navigate municipal requirements without relying entirely on high-cost external advisory services.
            </div>
          </div>
        </div>
      </section>

      {/* ── 3. Value Proposition (Why GovGuide AI?) ─────────────── */}
      <section style={{ marginBottom: 48 }} aria-labelledby="value-prop-heading">
        <div style={{ marginBottom: 20 }}>
          <h2 id="value-prop-heading" style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Why GovGuide AI?
          </h2>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            Combining intelligent information retrieval, multi-agent verification, and Responsible AI controls.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: 16,
          }}
        >
          {/* Card 01 */}
          <div className="card" style={{ display: 'flex', gap: 14, padding: 20 }}>
            <span style={{ fontSize: 14, fontWeight: 800, color: 'var(--color-blue)', background: '#eff6ff', borderRadius: 'var(--radius-sm)', width: 34, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              01
            </span>
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4, color: 'var(--color-text-primary)' }}>
                Faster Information Discovery
              </h3>
              <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
                Natural-language search replaces manual navigation across fragmented municipal information. Designed to significantly reduce information discovery time.
              </p>
            </div>
          </div>

          {/* Card 02 */}
          <div className="card" style={{ display: 'flex', gap: 14, padding: 20 }}>
            <span style={{ fontSize: 14, fontWeight: 800, color: 'var(--color-success)', background: '#f0fdf4', borderRadius: 'var(--radius-sm)', width: 34, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              02
            </span>
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4, color: 'var(--color-text-primary)' }}>
                Evidence-Grounded Guidance
              </h3>
              <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
                Responses are synthesized from retrieved official municipal records with a strict zero-fabrication grounding policy.
              </p>
            </div>
          </div>

          {/* Card 03 */}
          <div className="card" style={{ display: 'flex', gap: 14, padding: 20 }}>
            <span style={{ fontSize: 14, fontWeight: 800, color: '#6366f1', background: '#eef2ff', borderRadius: 'var(--radius-sm)', width: 34, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              03
            </span>
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4, color: 'var(--color-text-primary)' }}>
                Full Source Transparency
              </h3>
              <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
                Responses provide verifiable citations, ordinance information, and official agency links for transparent auditing.
              </p>
            </div>
          </div>

          {/* Card 04 */}
          <div className="card" style={{ display: 'flex', gap: 14, padding: 20 }}>
            <span style={{ fontSize: 14, fontWeight: 800, color: '#8b5cf6', background: '#faf5ff', borderRadius: 'var(--radius-sm)', width: 34, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              04
            </span>
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4, color: 'var(--color-text-primary)' }}>
                Multi-Agent Architecture
              </h3>
              <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
                Query Understanding, Hybrid Retrieval, and Response Verification agents work together with explicit protocol contracts.
              </p>
            </div>
          </div>

          {/* Card 05 */}
          <div className="card" style={{ display: 'flex', gap: 14, padding: 20 }}>
            <span style={{ fontSize: 14, fontWeight: 800, color: '#ec4899', background: '#fdf2f8', borderRadius: 'var(--radius-sm)', width: 34, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              05
            </span>
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4, color: 'var(--color-text-primary)' }}>
                Domain-Aware Retrieval
              </h3>
              <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
                Domain gating prevents irrelevant cross-domain retrieval such as driver's-license queries being matched with business licenses.
              </p>
            </div>
          </div>

          {/* Card 06 */}
          <div className="card" style={{ display: 'flex', gap: 14, padding: 20 }}>
            <span style={{ fontSize: 14, fontWeight: 800, color: '#14b8a6', background: '#f0fdfa', borderRadius: 'var(--radius-sm)', width: 34, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              06
            </span>
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4, color: 'var(--color-text-primary)' }}>
                Responsible AI & Security
              </h3>
              <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
                Prompt injection protection, rate limiting, audit logging, grounding controls, and transparent disclaimers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── 4. Proposed Pricing Section ─────────────────────────── */}
      <section style={{ marginBottom: 48 }} aria-labelledby="pricing-heading">
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4, flexWrap: 'wrap' }}>
            <h2 id="pricing-heading" style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-primary)', margin: 0 }}>
              Proposed Pricing Model
            </h2>
            <span
              style={{
                fontSize: 10,
                fontWeight: 700,
                textTransform: 'uppercase',
                background: '#f1f5f9',
                color: '#475569',
                padding: '2px 8px',
                borderRadius: 4,
                letterSpacing: '0.04em',
              }}
            >
              PROPOSED COMMERCIAL MODEL
            </span>
          </div>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            A tiered model designed to keep citizen access open while supporting professional and enterprise deployments.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: 24,
            alignItems: 'stretch',
          }}
        >
          {/* FREE */}
          <div
            className="card"
            style={{
              padding: 28,
              display: 'flex',
              flexDirection: 'column',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div style={{ marginBottom: 16 }}>
              <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-text-muted)', letterSpacing: '0.06em' }}>
                Citizen Discovery
              </span>
              <h3 style={{ fontSize: 22, fontWeight: 700, color: 'var(--color-text-primary)', margin: '4px 0 8px' }}>
                Free
              </h3>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                <span style={{ fontSize: 32, fontWeight: 800, color: 'var(--color-text-primary)' }}>$0</span>
                <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>/ month</span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 8, marginBottom: 0 }}>
                For individual citizens and first-time entrepreneurs.
              </p>
            </div>

            <div style={{ borderTop: '1px solid var(--color-border-light)', paddingTop: 20, marginBottom: 24, flex: 1 }}>
              <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-text-secondary)', marginBottom: 12, letterSpacing: '0.04em' }}>
                Included Features:
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  <Check size={16} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: 2 }} />
                  <span>Unlimited natural-language service lookups</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  <Check size={16} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: 2 }} />
                  <span>Access to 56 official Chicago service profiles</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  <Check size={16} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: 2 }} />
                  <span>Basic eligibility & fee guidance</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  <Check size={16} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: 2 }} />
                  <span>Standard web interface</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  <Check size={16} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: 2 }} />
                  <span>Official source citations & links</span>
                </li>
              </ul>
            </div>

            <div
              style={{
                background: 'var(--color-surface-2)',
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                textAlign: 'center',
                fontSize: 11,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                color: 'var(--color-text-secondary)',
              }}
            >
              PROPOSED ACADEMIC PLAN
            </div>
          </div>

          {/* PROFESSIONAL */}
          <div
            className="card"
            style={{
              padding: 28,
              display: 'flex',
              flexDirection: 'column',
              borderRadius: 'var(--radius-md)',
              border: '2px solid var(--color-accent)',
              boxShadow: '0 8px 24px -4px rgba(99, 102, 241, 0.12)',
              position: 'relative',
              background: 'linear-gradient(180deg, #ffffff 0%, #faf5ff 100%)',
            }}
          >
            <div style={{ marginBottom: 16 }}>
              <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-accent)', letterSpacing: '0.06em' }}>
                Advisory & Expeditors
              </span>
              <h3 style={{ fontSize: 22, fontWeight: 700, color: 'var(--color-text-primary)', margin: '4px 0 8px' }}>
                Professional
              </h3>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 32, fontWeight: 800, color: 'var(--color-text-primary)' }}>$49</span>
                <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>/ month</span>
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-accent)', background: 'rgba(99, 102, 241, 0.1)', padding: '2px 8px', borderRadius: 4 }}>
                  $490 / year
                </span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 8, marginBottom: 0 }}>
                For consultants, CPAs, and permit expeditors managing multiple clients.
              </p>
            </div>

            <div style={{ borderTop: '1px solid rgba(99, 102, 241, 0.15)', paddingTop: 20, marginBottom: 24, flex: 1 }}>
              <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-accent)', marginBottom: 12, letterSpacing: '0.04em' }}>
                Everything in Free, plus:
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-primary)' }}>
                  <Check size={16} style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: 2 }} />
                  <span><strong>Priority LLM</strong> response generation</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-primary)' }}>
                  <Check size={16} style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: 2 }} />
                  <span><strong>Multi-session</strong> context</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-primary)' }}>
                  <Check size={16} style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: 2 }} />
                  <span>Document checklists</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-primary)' }}>
                  <Check size={16} style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: 2 }} />
                  <span>Exportable compliance summaries</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-primary)' }}>
                  <Check size={16} style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: 2 }} />
                  <span>Up to 500 AI agent queries / month</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-primary)' }}>
                  <Check size={16} style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: 2 }} />
                  <span>Email & priority chat advisory support</span>
                </li>
              </ul>
            </div>

            <div
              style={{
                background: 'rgba(99, 102, 241, 0.1)',
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                textAlign: 'center',
                fontSize: 11,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                color: 'var(--color-accent)',
              }}
            >
              PROPOSED COMMERCIAL PLAN
            </div>
          </div>

          {/* ENTERPRISE */}
          <div
            className="card"
            style={{
              padding: 28,
              display: 'flex',
              flexDirection: 'column',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div style={{ marginBottom: 16 }}>
              <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-text-muted)', letterSpacing: '0.06em' }}>
                Municipal & Agencies
              </span>
              <h3 style={{ fontSize: 22, fontWeight: 700, color: 'var(--color-text-primary)', margin: '4px 0 8px' }}>
                Enterprise
              </h3>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 32, fontWeight: 800, color: 'var(--color-text-primary)' }}>Custom</span>
                <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>(From $2,500 / month proposed starting price)</span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 8, marginBottom: 0 }}>
                For city departments, 311 contact centers, and regional government authorities.
              </p>
            </div>

            <div style={{ borderTop: '1px solid var(--color-border-light)', paddingTop: 20, marginBottom: 24, flex: 1 }}>
              <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-text-secondary)', marginBottom: 12, letterSpacing: '0.04em' }}>
                Enterprise Inclusions:
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  <Check size={16} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: 2 }} />
                  <span>Dedicated multi-agent tenant deployment</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  <Check size={16} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: 2 }} />
                  <span>Custom municipal dataset ingestion</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  <Check size={16} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: 2 }} />
                  <span>REST API & Agent Protocol access</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  <Check size={16} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: 2 }} />
                  <span>Proposed 99.9% uptime SLA</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  <Check size={16} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: 2 }} />
                  <span>Dedicated account management</span>
                </li>
                <li style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  <Check size={16} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: 2 }} />
                  <span>On-premise or sovereign cloud hosting</span>
                </li>
              </ul>
            </div>

            <div
              style={{
                background: 'var(--color-surface-2)',
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                textAlign: 'center',
                fontSize: 11,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                color: 'var(--color-text-secondary)',
              }}
            >
              PROPOSED ENTERPRISE PLAN
            </div>
          </div>
        </div>
      </section>

      {/* ── 5. Revenue Model ────────────────────────────────────── */}
      <section style={{ marginBottom: 48 }} aria-labelledby="revenue-heading">
        <div style={{ marginBottom: 20 }}>
          <h2 id="revenue-heading" style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Revenue Model
          </h2>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            Proposed revenue streams and operating assumptions for commercial scale.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: 16,
          }}
        >
          {/* Stream 01 */}
          <div className="card" style={{ padding: 22 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <span style={{ fontSize: 12, fontWeight: 800, color: '#2563eb', background: '#eff6ff', borderRadius: 'var(--radius-sm)', padding: '4px 8px' }}>
                01
              </span>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', margin: 0 }}>
                SaaS Subscriptions
              </h3>
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Recurring monthly and annual subscriptions from professional users and licensing advisors.
            </p>
          </div>

          {/* Stream 02 */}
          <div className="card" style={{ padding: 22 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <span style={{ fontSize: 12, fontWeight: 800, color: '#10b981', background: '#f0fdf4', borderRadius: 'var(--radius-sm)', padding: '4px 8px' }}>
                02
              </span>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', margin: 0 }}>
                Municipal Government Licensing
              </h3>
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Enterprise contracts for municipal portals, 311 contact centers, and white-label deployments.
            </p>
          </div>

          {/* Stream 03 */}
          <div className="card" style={{ padding: 22 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <span style={{ fontSize: 12, fontWeight: 800, color: '#6366f1', background: '#eef2ff', borderRadius: 'var(--radius-sm)', padding: '4px 8px' }}>
                03
              </span>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', margin: 0 }}>
                API Access & Webhooks
              </h3>
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Usage-based API access for potential integration targets (e.g. legal, compliance, and permit-management platforms).
            </p>
          </div>

          {/* Stream 04 */}
          <div className="card" style={{ padding: 22 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <span style={{ fontSize: 12, fontWeight: 800, color: '#d97706', background: '#fffbeb', borderRadius: 'var(--radius-sm)', padding: '4px 8px' }}>
                04
              </span>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', margin: 0 }}>
                Custom Municipal Data Integration
              </h3>
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              One-time onboarding services for digitizing, chunking, and indexing new municipal knowledge sources.
            </p>
          </div>
        </div>
      </section>

      {/* ── 6. Unit Economics ───────────────────────────────────── */}
      <section style={{ marginBottom: 48 }} aria-labelledby="economics-heading">
        <div style={{ marginBottom: 20 }}>
          <h2 id="economics-heading" style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Cost Structure & Unit Economics
          </h2>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            Operating cost assumptions and gross margin projections.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 20,
            marginBottom: 16,
          }}
        >
          {/* Card 1 */}
          <div className="card" style={{ padding: 24, borderTop: '3px solid #3b82f6' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Infrastructure
              </span>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#2563eb', background: '#eff6ff', padding: '2px 6px', borderRadius: 4 }}>
                PROPOSED / ESTIMATED
              </span>
            </div>
            <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--color-text-primary)', marginBottom: 8 }}>
              ~$150 <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-text-muted)' }}>/ month</span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Estimated managed PostgreSQL/pgvector, FastAPI infrastructure, and CDN baseline.
            </p>
          </div>

          {/* Card 2 */}
          <div className="card" style={{ padding: 24, borderTop: '3px solid #6366f1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                LLM Inference
              </span>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#6366f1', background: '#eef2ff', padding: '2px 6px', borderRadius: 4 }}>
                PROPOSED / ESTIMATED
              </span>
            </div>
            <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--color-text-primary)', marginBottom: 8 }}>
              ~$0.002 <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-text-muted)' }}>/ query</span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Proposed estimated inference assumption using cost-efficient model routing and local fallback.
            </p>
          </div>

          {/* Card 3 */}
          <div className="card" style={{ padding: 24, borderTop: '3px solid #10b981' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Projected Gross Margin
              </span>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#10b981', background: '#f0fdf4', padding: '2px 6px', borderRadius: 4 }}>
                PROPOSED / ESTIMATED
              </span>
            </div>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#166534', marginBottom: 8 }}>
              82% – 88%
            </div>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Projected academic estimate at scale with minimal incremental retrieval costs.
            </p>
          </div>
        </div>

        {/* Academic Footnote */}
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', fontStyle: 'italic', paddingLeft: 4 }}>
          * Financial figures are academic assumptions for commercialization planning and have not been validated through production billing data.
        </div>
      </section>

      {/* ── 7. Deployment Strategy ──────────────────────────────── */}
      <section style={{ marginBottom: 48 }} aria-labelledby="deployment-heading">
        <div style={{ marginBottom: 20 }}>
          <h2 id="deployment-heading" style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Deployment Strategy
          </h2>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            Separating the current academic prototype from the proposed commercial production architecture.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: 20,
          }}
        >
          {/* CURRENT PROJECT PROTOTYPE */}
          <div className="card" style={{ padding: 24, borderLeft: '4px solid #3b82f6' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Server size={20} style={{ color: '#2563eb' }} />
                <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                  CURRENT PROJECT PROTOTYPE
                </h3>
              </div>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#1d4ed8', background: '#dbeafe', padding: '3px 8px', borderRadius: 4, letterSpacing: '0.04em' }}>
                IMPLEMENTED
              </span>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: 'var(--color-blue)', flexShrink: 0 }} />
                <span>FastAPI backend + React 19 SPA</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: 'var(--color-blue)', flexShrink: 0 }} />
                <span>56 official City of Chicago BACP service records</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: 'var(--color-blue)', flexShrink: 0 }} />
                <span>Hybrid BM25 + dense vector RAG with RRF</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: 'var(--color-blue)', flexShrink: 0 }} />
                <span>Domain-aware retrieval gating</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: 'var(--color-blue)', flexShrink: 0 }} />
                <span>Prompt injection defenses</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: 'var(--color-blue)', flexShrink: 0 }} />
                <span>Multi-agent architecture</span>
              </li>
            </ul>
          </div>

          {/* PROPOSED COMMERCIAL DEPLOYMENT */}
          <div className="card" style={{ padding: 24, borderLeft: '4px solid #6366f1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Cloud size={20} style={{ color: '#6366f1' }} />
                <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                  PROPOSED COMMERCIAL DEPLOYMENT
                </h3>
              </div>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#6366f1', background: '#eef2ff', padding: '3px 8px', borderRadius: 4, letterSpacing: '0.04em' }}>
                FUTURE / PROPOSED
              </span>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13, color: 'var(--color-text-secondary)' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: '#6366f1', flexShrink: 0 }} />
                <span>Multi-tenant Kubernetes on AWS / Azure</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: '#6366f1', flexShrink: 0 }} />
                <span>Distributed pgvector / Milvus</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: '#6366f1', flexShrink: 0 }} />
                <span>Sovereign/on-premise deployment for government agencies</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: '#6366f1', flexShrink: 0 }} />
                <span>Public REST API</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: '#6366f1', flexShrink: 0 }} />
                <span>OAuth2 and webhooks</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={15} style={{ color: '#6366f1', flexShrink: 0 }} />
                <span>Organization-level deployment</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* ── 8. Go-To-Market Roadmap ─────────────────────────────── */}
      <section style={{ marginBottom: 48 }} aria-labelledby="gtm-heading">
        <div style={{ marginBottom: 20 }}>
          <h2 id="gtm-heading" style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Go-To-Market Strategy
          </h2>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            Proposed expansion from a local Chicago pilot to regional municipal scaling.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 20,
          }}
        >
          {/* Phase 01 */}
          <div className="card" style={{ padding: 22, position: 'relative' }}>
            <div style={{ display: 'inline-block', background: '#eff6ff', color: '#2563eb', fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 4, textTransform: 'uppercase', marginBottom: 12 }}>
              PHASE 01 • LOCAL LAUNCH
            </div>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 10 }}>
              Chicago BACP Pilot
            </h3>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, color: 'var(--color-text-secondary)' }}>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <ArrowRight size={14} style={{ color: '#2563eb', flexShrink: 0, marginTop: 3 }} />
                <span>Engage Chambers of Commerce and SBDCs</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <ArrowRight size={14} style={{ color: '#2563eb', flexShrink: 0, marginTop: 3 }} />
                <span>Launch community web portal</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <ArrowRight size={14} style={{ color: '#2563eb', flexShrink: 0, marginTop: 3 }} />
                <span>Focus on Chicago entrepreneurs and startups</span>
              </li>
            </ul>
          </div>

          {/* Phase 02 */}
          <div className="card" style={{ padding: 22, position: 'relative' }}>
            <div style={{ display: 'inline-block', background: '#eef2ff', color: '#6366f1', fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 4, textTransform: 'uppercase', marginBottom: 12 }}>
              PHASE 02 • B2B EXPANSION
            </div>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 10 }}>
              Advisory & Legal Partnerships
            </h3>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, color: 'var(--color-text-secondary)' }}>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <ArrowRight size={14} style={{ color: '#6366f1', flexShrink: 0, marginTop: 3 }} />
                <span>CPA firms</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <ArrowRight size={14} style={{ color: '#6366f1', flexShrink: 0, marginTop: 3 }} />
                <span>Professional business expeditors</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <ArrowRight size={14} style={{ color: '#6366f1', flexShrink: 0, marginTop: 3 }} />
                <span>Launch Professional tier</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <ArrowRight size={14} style={{ color: '#6366f1', flexShrink: 0, marginTop: 3 }} />
                <span>Multi-client compliance capabilities</span>
              </li>
            </ul>
          </div>

          {/* Phase 03 */}
          <div className="card" style={{ padding: 22, position: 'relative' }}>
            <div style={{ display: 'inline-block', background: '#f0fdf4', color: '#10b981', fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 4, textTransform: 'uppercase', marginBottom: 12 }}>
              PHASE 03 • REGIONAL SCALING
            </div>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 10 }}>
              Illinois & Midwest Expansion
            </h3>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, color: 'var(--color-text-secondary)' }}>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <ArrowRight size={14} style={{ color: '#10b981', flexShrink: 0, marginTop: 3 }} />
                <span>Expand municipal knowledge ingestion</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <ArrowRight size={14} style={{ color: '#10b981', flexShrink: 0, marginTop: 3 }} />
                <span>Target Cook County and regional municipalities</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <ArrowRight size={14} style={{ color: '#10b981', flexShrink: 0, marginTop: 3 }} />
                <span>Explore municipal SaaS licensing</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* ── 9. Responsible AI by Design ─────────────────────────── */}
      <section style={{ marginBottom: 48 }} aria-labelledby="responsible-ai-heading">
        <div style={{ marginBottom: 20 }}>
          <h2 id="responsible-ai-heading" style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Responsible AI by Design
          </h2>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            Trust, transparency, and verification are core product requirements for government technology.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: 16,
          }}
        >
          <div className="card" style={{ padding: 22 }}>
            <div style={{ color: 'var(--color-success)', marginBottom: 12 }}>
              <BadgeCheck size={24} />
            </div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>
              Grounding & Verification
            </h3>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Answers are generated from verified knowledge sources and safely refuse when evidence is insufficient.
            </p>
          </div>

          <div className="card" style={{ padding: 22 }}>
            <div style={{ color: 'var(--color-accent)', marginBottom: 12 }}>
              <ShieldCheck size={24} />
            </div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>
              Prompt Injection Defense
            </h3>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Override phrases, jailbreak patterns, and prompt manipulation attempts are detected before sensitive execution.
            </p>
          </div>

          <div className="card" style={{ padding: 22 }}>
            <div style={{ color: 'var(--color-blue)', marginBottom: 12 }}>
              <Scale size={24} />
            </div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>
              Domain-Aware Retrieval
            </h3>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Unsupported domains are detected before retrieval, preventing irrelevant cross-domain answers.
            </p>
          </div>

          <div className="card" style={{ padding: 22 }}>
            <div style={{ color: '#a855f7', marginBottom: 12 }}>
              <Eye size={24} />
            </div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>
              Source Transparency
            </h3>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Responses expose official source information and verification guidance.
            </p>
          </div>
        </div>
      </section>

      {/* ── 10. Why Agentic Architecture Matters ────────────────── */}
      <section style={{ marginBottom: 48 }} aria-labelledby="agentic-heading">
        <div style={{ marginBottom: 20 }}>
          <h2 id="agentic-heading" style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Why the Agentic Architecture Matters
          </h2>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: 0 }}>
            How multi-agent specialization translates technical capability into commercial value.
          </p>
        </div>

        {/* Horizontal Agent Flow */}
        <div className="card" style={{ padding: 24, marginBottom: 20, background: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: 16,
              alignItems: 'stretch',
            }}
          >
            {/* Agent 1 */}
            <div style={{ background: '#ffffff', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, color: '#2563eb' }}>
                <Bot size={18} />
                <span style={{ fontSize: 13, fontWeight: 700 }}>QUERY AGENT</span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
                Understands intent and entities
              </div>
            </div>

            {/* Agent 2 */}
            <div style={{ background: '#ffffff', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, color: '#6366f1' }}>
                <Database size={18} />
                <span style={{ fontSize: 13, fontWeight: 700 }}>RETRIEVAL AGENT</span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
                Finds and ranks evidence
              </div>
            </div>

            {/* Agent 3 */}
            <div style={{ background: '#ffffff', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, color: '#10b981' }}>
                <ShieldCheck size={18} />
                <span style={{ fontSize: 13, fontWeight: 700 }}>VERIFICATION AGENT</span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
                Validates grounding and citations
              </div>
            </div>

            {/* Commercial Impact */}
            <div style={{ background: 'linear-gradient(135deg, #1e3a8a, #2563eb)', color: '#ffffff', borderRadius: 'var(--radius-sm)', padding: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <Sparkles size={18} />
                <span style={{ fontSize: 13, fontWeight: 700 }}>BUSINESS VALUE</span>
              </div>
              <div style={{ fontSize: 12, opacity: 0.95, lineHeight: 1.4 }}>
                Reliable government-service discovery
              </div>
            </div>
          </div>
        </div>

        {/* 3 Business Value Cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 16,
          }}
        >
          <div className="card" style={{ padding: 20 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>
              Faster Discovery
            </h3>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Reduce manual searching across fragmented government information.
            </p>
          </div>

          <div className="card" style={{ padding: 20 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>
              Lower Support Burden
            </h3>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Enable self-service guidance for repetitive information requests.
            </p>
          </div>

          <div className="card" style={{ padding: 20 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>
              Reduced Regulatory Risk
            </h3>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Ground answers in verified evidence and provide official source references.
            </p>
          </div>
        </div>
      </section>

      {/* ── 11. Commercialization Summary (At a Glance) ──────────── */}
      <section aria-labelledby="summary-heading">
        <div className="card" style={{ padding: 28, border: '1px solid var(--color-border)', background: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)' }}>
          <div style={{ marginBottom: 20, textAlign: 'center' }}>
            <h2 id="summary-heading" style={{ fontSize: 18, fontWeight: 800, color: 'var(--color-text-primary)', margin: 0 }}>
              GovGuide AI Commercialization at a Glance
            </h2>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 20,
              borderTop: '1px solid var(--color-border)',
              borderBottom: '1px solid var(--color-border)',
              padding: '20px 0',
              marginBottom: 16,
            }}
          >
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 4, letterSpacing: '0.04em' }}>
                TARGET
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Citizens • Businesses • Government • NGOs
              </div>
            </div>

            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 4, letterSpacing: '0.04em' }}>
                MODEL
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                SaaS • B2G • API
              </div>
            </div>

            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 4, letterSpacing: '0.04em' }}>
                PRICING
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Free • $49/mo • Enterprise
              </div>
            </div>

            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 4, letterSpacing: '0.04em' }}>
                DEPLOYMENT
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Cloud • Private • Sovereign
              </div>
            </div>
          </div>

          <div style={{ textAlign: 'center', fontSize: 12, color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
            Academic commercialization proposal — not an active billing system.
          </div>
        </div>
      </section>
    </div>
  )
}
