import { ShieldCheck } from 'lucide-react'

/**
 * ConfidenceBadge
 *
 * Maps backend confidence_label to a citizen-friendly label.
 * Never displays raw numeric confidence scores.
 *
 * Props:
 *   confidenceLabel {string} - 'high' | 'medium' | 'low' | any
 */

const CONFIDENCE_MAP = {
  high: {
    label: 'High confidence',
    className: 'confidence-badge high',
  },
  medium: {
    label: 'Moderate confidence',
    className: 'confidence-badge medium',
  },
  low: {
    label: 'Low confidence',
    className: 'confidence-badge low',
  },
}

export default function ConfidenceBadge({ confidenceLabel }) {
  const config = CONFIDENCE_MAP[confidenceLabel] ?? {
    label: 'Confidence unknown',
    className: 'confidence-badge insufficient',
  }

  return (
    <span className={config.className}>
      <ShieldCheck size={12} aria-hidden="true" />
      <span>{config.label}</span>
    </span>
  )
}
