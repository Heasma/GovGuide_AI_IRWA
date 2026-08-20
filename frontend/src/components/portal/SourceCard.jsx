import { ExternalLink, Globe } from 'lucide-react'

/**
 * SourceCard
 *
 * Renders a single official government source.
 * Only uses URLs supplied by the backend — never invents URLs.
 *
 * Props:
 *   source {object} - Backend source object:
 *     { title, url, excerpt, domain, source_id }
 *   index {number}  - Display index (1-based)
 */

function extractDomain(url) {
  if (!url || typeof url !== 'string') return null
  try {
    const parsed = new URL(url)
    return parsed.hostname.replace(/^www\./, '')
  } catch {
    return null
  }
}

function isValidUrl(url) {
  if (!url || typeof url !== 'string') return false
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

export default function SourceCard({ source, index }) {
  const { title, url, excerpt } = source
  const domain = source.domain || extractDomain(url)
  const hasUrl = isValidUrl(url)

  return (
    <div className="source-card">
      <div className="source-card-header">
        <div className="source-card-index">{index}</div>
        <div className="source-card-meta">
          <h4 className="source-card-title">{title || 'Official Source'}</h4>
          {domain && (
            <div className="source-card-domain">
              <Globe size={11} aria-hidden="true" />
              <span>{domain}</span>
            </div>
          )}
        </div>
      </div>

      {excerpt && (
        <p className="source-card-excerpt">{excerpt}</p>
      )}

      <div className="source-card-footer">
        {hasUrl ? (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="source-card-cta"
            aria-label={`View official source: ${title || 'Official Source'}`}
          >
            View Official Source
            <ExternalLink size={12} aria-hidden="true" />
          </a>
        ) : (
          <span
            className="source-card-cta source-card-cta--disabled"
            aria-label="Source URL not available"
          >
            View Official Source
            <ExternalLink size={12} aria-hidden="true" />
          </span>
        )}
      </div>
    </div>
  )
}
