import type { TriageAnalyzeResponse } from '../api/types'

interface TriageSuggestionPanelProps {
  suggestion: TriageAnalyzeResponse | null
}

const URGENCY_LABELS: Record<string, string> = {
  routine: 'Routine',
  priority: 'Priority',
  urgent: 'Urgent',
}

const DEPT_LABELS: Record<string, string> = {
  general_medicine: 'General Medicine',
  cardiology: 'Cardiology',
  neurology: 'Neurology',
  orthopedics: 'Orthopedics',
  dermatology: 'Dermatology',
  ent: 'ENT',
  pulmonology: 'Pulmonology',
  gastroenterology: 'Gastroenterology',
  emergency: 'Emergency',
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100)
  const color = confidence >= 0.7
    ? 'var(--urgency-routine)'
    : confidence >= 0.5
    ? 'var(--urgency-priority)'
    : 'var(--urgency-urgent)'

  return (
    <div style={{ marginTop: 8 }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: 11,
        color: 'var(--color-text-muted)',
        marginBottom: 4,
      }}>
        <span>Confidence</span>
        <span style={{ color, fontWeight: 600 }}>{pct}%</span>
      </div>
      <div style={{
        height: 6,
        borderRadius: 3,
        background: 'var(--color-border)',
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%',
          width: `${pct}%`,
          background: color,
          borderRadius: 3,
          transition: 'width 0.3s ease',
        }} />
      </div>
    </div>
  )
}

function UrgencyBadge({ urgency }: { urgency: string }) {
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '2px 8px',
      borderRadius: 'var(--radius-full)',
      fontSize: 11,
      fontWeight: 600,
      background: `var(--urgency-${urgency}-bg)`,
      color: `var(--urgency-${urgency}-text)`,
      border: `1px solid var(--urgency-${urgency}-border)`,
    }}>
      {URGENCY_LABELS[urgency] ?? urgency}
    </span>
  )
}

export default function TriageSuggestionPanel({ suggestion }: TriageSuggestionPanelProps) {
  if (!suggestion) return null

  const isLowConfidence = suggestion.confidence !== null && suggestion.confidence < 0.5
  const sourceLabel = suggestion.source === 'rule_engine' ? 'Rule Engine' : 'AI'
  const sourceColor = suggestion.source === 'rule_engine'
    ? 'var(--color-primary)'
    : 'var(--color-text-secondary)'

  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-lg)',
      padding: '16px',
      marginBottom: 20,
    }}>
      {/* Header row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            fontSize: 11,
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: sourceColor,
          }}>
            {sourceLabel}
          </span>
          {isLowConfidence && (
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 3,
              padding: '2px 8px',
              borderRadius: 'var(--radius-full)',
              fontSize: 11,
              fontWeight: 600,
              background: 'var(--urgency-priority-bg)',
              color: 'var(--urgency-priority-text)',
              border: '1px solid var(--urgency-priority-border)',
            }}>
              Low confidence — please review
            </span>
          )}
        </div>
      </div>

      {/* Suggestion details */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '8px 16px',
        marginBottom: suggestion.confidence !== null ? 12 : 0,
      }}>
        <div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 2 }}>
            Suggested Urgency
          </div>
          <UrgencyBadge urgency={suggestion.urgency} />
        </div>
        <div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 2 }}>
            Suggested Department
          </div>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            {DEPT_LABELS[suggestion.department] ?? suggestion.department}
          </div>
        </div>
      </div>

      {/* Confidence bar */}
      {suggestion.confidence !== null && (
        <ConfidenceBar confidence={suggestion.confidence} />
      )}

      {/* Reasoning */}
      {suggestion.reasoning && (
        <div style={{
          marginTop: 10,
          padding: '8px 10px',
          background: 'var(--color-surface-raised)',
          borderRadius: 'var(--radius-md)',
          fontSize: 12,
          color: 'var(--color-text-secondary)',
          fontStyle: 'italic',
        }}>
          {suggestion.reasoning}
        </div>
      )}
    </div>
  )
}
