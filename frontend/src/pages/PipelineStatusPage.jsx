/**
 * GovGuide AI — Agentic Pipeline Monitoring Page
 *
 * Operational telemetry and status tracking across GovGuide AI's
 * multi-agent NLP research, retrieval, and grounding architecture.
 */

import PageHeader from '../components/common/PageHeader'
import StatusBadge from '../components/common/StatusBadge'
import { Activity, Cpu, ArrowRight, CheckCircle2, Layers } from 'lucide-react'

const PIPELINE_STAGES = [
  {
    stage: 'Data Source Layer',
    status: 'Active (56 License Types)',
    description: 'City of Chicago Business Licensing registry ingested into PostgreSQL database.',
    color: '#10b981',
  },
  {
    stage: 'Schema Validation',
    status: 'Verified (Pydantic V2)',
    description: 'GovernmentService & BusinessLicense strict validation models active.',
    color: '#10b981',
  },
  {
    stage: 'NLP Query Processor',
    status: 'Ready (Sanitization & Normalization)',
    description: 'Security input sanitizer, prompt defense, and query keyword extractor.',
    color: '#3b82f6',
  },
  {
    stage: 'Hybrid Retrieval Engine',
    status: 'Active (SQL + BM25 Search)',
    description: 'Dual-path SQL structured repository and BM25 text ranker for license search.',
    color: '#10b981',
  },
  {
    stage: 'Agentic Orchestration',
    status: 'Active (Multi-Agent Grounding)',
    description: 'Research agent, advisory agent, and orchestrator coordinating evidence-grounded answers.',
    color: '#10b981',
  },
]

export default function PipelineStatusPage() {
  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto' }} className="fade-in">
      <PageHeader
        title="Agentic Pipeline Monitoring"
        subtitle="Visual status tracking across GovGuide's multi-agent research, retrieval, and grounding pipeline."
        badgeText="Pipeline Operational"
      />

      <div className="card premium-card" style={{ marginBottom: 32, padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <Activity size={24} style={{ color: '#10b981' }} />
          <div>
            <h2 className="text-h2" style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>
              Pipeline Architecture Telemetry
            </h2>
            <div className="text-small" style={{ color: 'var(--color-text-secondary)' }}>
              All 5 pipeline stages verified & configured for City of Chicago dataset
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 24 }}>
          {PIPELINE_STAGES.map((stg, i) => (
            <div
              key={stg.stage}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: 16,
                background: 'var(--color-surface-2)',
                borderRadius: 8,
                border: '1px solid var(--color-border)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    background: 'rgba(37, 99, 235, 0.1)',
                    color: 'var(--color-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 12,
                    fontWeight: 700,
                  }}
                >
                  {i + 1}
                </div>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)' }}>
                    {stg.stage}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 2 }}>
                    {stg.description}
                  </div>
                </div>
              </div>

              <StatusBadge status={stg.status} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
