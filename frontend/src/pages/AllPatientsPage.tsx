/**
 * src/pages/AllPatientsPage.tsx — Phase 8 All Patients Page + Phase 9 Patient Detail Modal.
 *
 * Phase 8 — All Patients Page:
 * 8.1  Filter Bar — name (debounced 300ms), date range, urgency/department dropdowns, clear
 * 8.2  Results Table — Patient, Age, Gender, Urgency (badge), Department, Source, Time, Actions
 * 8.2  Pagination — prev/next + page indicator, 20 per page
 * 8.3  Empty States — no results for filters vs no patients at all
 *
 * Phase 9 — Patient Detail Modal:
 * 9.1  URL Sync — /patients?id=<uuid> on open, /patients on close, back button closes modal
 * 9.1  Page load with ?id= — modal auto-opens and fetches record
 * 9.2  Modal Content — patient info, symptoms, AI panel (if AI used), final decision, override status
 */
import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import type { IntakeOut } from '../api/types'
import {
  useIntakeList,
  useIntakeDetail,
  useMetaDepartments,
  useMetaUrgencyLevels,
} from '../api/hooks'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const PAGE_SIZE = 20

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

const URGENCY_LABELS: Record<string, string> = {
  routine: 'Routine',
  priority: 'Priority',
  urgent: 'Urgent',
}

// ---------------------------------------------------------------------------
// Source / Override status computation
// ---------------------------------------------------------------------------
function computeSource(record: IntakeOut): string {
  if (record.triage_source === null) return 'Manual'
  if (!record.urgency_overridden && !record.department_overridden) return 'AI accepted'
  return 'Overridden'
}

function computeOverrideLabel(record: IntakeOut): string {
  if (record.triage_source === null) return 'Manual entry'
  const u = record.urgency_overridden
  const d = record.department_overridden
  if (!u && !d) return 'AI accepted'
  if (u && d) return 'Both overridden'
  if (u) return 'Urgency overridden'
  return 'Department overridden'
}

// ---------------------------------------------------------------------------
// Urgency Badge
// ---------------------------------------------------------------------------
function UrgencyBadge({ urgency }: { urgency: string }) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: 'var(--radius-full)',
        fontSize: 11,
        fontWeight: 600,
        background: `var(--urgency-${urgency}-bg)`,
        color: `var(--urgency-${urgency}-text)`,
        border: `1px solid var(--urgency-${urgency}-border)`,
      }}
    >
      {URGENCY_LABELS[urgency] ?? urgency}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Source Badge
// ---------------------------------------------------------------------------
function SourceBadge({ source }: { source: string }) {
  const isManual = source === 'Manual'
  const isOverridden = source === 'Overridden'
  const color = isManual
    ? 'var(--color-text-muted)'
    : isOverridden
    ? 'var(--urgency-priority-text)'
    : 'var(--urgency-routine-text)'
  const bg = isManual
    ? 'var(--color-surface-raised)'
    : isOverridden
    ? 'var(--urgency-priority-bg)'
    : 'var(--urgency-routine-bg)'
  const border = isManual
    ? 'var(--color-border)'
    : isOverridden
    ? 'var(--urgency-priority-border)'
    : 'var(--urgency-routine-border)'

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: 'var(--radius-full)',
        fontSize: 11,
        fontWeight: 600,
        color,
        background: bg,
        border: `1px solid ${border}`,
      }}
    >
      {source}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Override Status Badge
// ---------------------------------------------------------------------------
function OverrideStatusBadge({ label }: { label: string }) {
  const isAccepted = label === 'AI accepted'
  const isManual = label === 'Manual entry'
  const color = isManual
    ? 'var(--color-text-muted)'
    : isAccepted
    ? 'var(--urgency-routine-text)'
    : 'var(--urgency-priority-text)'
  const bg = isManual
    ? 'var(--color-surface-raised)'
    : isAccepted
    ? 'var(--urgency-routine-bg)'
    : 'var(--urgency-priority-bg)'
  const border = isManual
    ? 'var(--color-border)'
    : isAccepted
    ? 'var(--urgency-routine-border)'
    : 'var(--urgency-priority-border)'

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '4px 10px',
        borderRadius: 'var(--radius-md)',
        fontSize: 12,
        fontWeight: 600,
        color,
        background: bg,
        border: `1px solid ${border}`,
      }}
    >
      {label}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Empty State
// ---------------------------------------------------------------------------
function EmptyState({ hasFilters }: { hasFilters: boolean }) {
  return (
    <div
      style={{
        padding: '48px 20px',
        textAlign: 'center',
        color: 'var(--color-text-muted)',
        fontSize: 14,
      }}
    >
      {hasFilters
        ? 'No patients found matching your search'
        : 'No patients registered yet'}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Loading Skeleton
// ---------------------------------------------------------------------------
function SkeletonRow() {
  return (
    <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
      {[18, 8, 8, 10, 14, 10, 10, 8].map((w, i) => (
        <td key={i} style={{ padding: '12px 10px' }}>
          <div
            style={{
              height: 14,
              width: `${w * 8}px`,
              borderRadius: 4,
              background:
                'linear-gradient(90deg, var(--color-border) 25%, var(--color-surface-raised) 50%, var(--color-border) 75%)',
              backgroundSize: '200% 100%',
              animation: 'shimmer 1.4s ease-in-out infinite',
            }}
          />
        </td>
      ))}
    </tr>
  )
}

// ---------------------------------------------------------------------------
// Patient Detail Modal (Phase 9)
// ---------------------------------------------------------------------------
function PatientDetailModal({
  record,
  onClose,
}: {
  record: IntakeOut | null
  onClose: () => void
}) {
  const overrideLabel = record ? computeOverrideLabel(record) : ''
  const registeredAt = record
    ? new Date(record.created_at).toLocaleString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : ''

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-surface-overlay)',
        backdropFilter: 'blur(2px)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--color-surface)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-xl)',
          width: '100%',
          maxWidth: 600,
          maxHeight: '90vh',
          overflowY: 'auto',
          margin: 16,
        }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '20px 24px',
            borderBottom: '1px solid var(--color-border)',
          }}
        >
          <h2
            id="modal-title"
            style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text)', margin: 0 }}
          >
            Patient Detail
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: 22,
              color: 'var(--color-text-muted)',
              padding: 4,
              lineHeight: 1,
            }}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Content */}
        {record ? (
          <div style={{ padding: '24px' }}>
            {/* Patient Info */}
            <Section title="Patient Information">
              <InfoGrid>
                <InfoItem label="Name" value={record.patient.name} />
                <InfoItem label="Age" value={String(record.patient.age)} />
                <InfoItem label="Gender" value={record.patient.gender} />
                <InfoItem label="Contact" value={record.patient.contact_number} />
                <InfoItem
                  label="Registered At"
                  value={registeredAt}
                  span
                />
              </InfoGrid>
            </Section>

            {/* Symptoms */}
            <Section title="Symptoms">
              <div
                style={{
                  padding: '10px 12px',
                  background: 'var(--color-surface-raised)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 13,
                  color: 'var(--color-text)',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {record.symptoms_text}
              </div>
            </Section>

            {/* AI Suggestion Panel (if AI was used) */}
            {record.triage_source !== null && (
              <Section title="AI Suggestion">
                <div
                  style={{
                    padding: '12px 16px',
                    background: 'var(--color-surface-raised)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                  }}
                >
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '8px 16px',
                      marginBottom: 8,
                    }}
                  >
                    <div>
                      <div style={metaLabelStyle}>Source</div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-primary)' }}>
                        {record.triage_source === 'rule_engine' ? 'Rule Engine' : 'AI'}
                      </div>
                    </div>
                    <div>
                      <div style={metaLabelStyle}>Suggested Urgency</div>
                      <UrgencyBadge urgency={record.ai_suggested_urgency ?? 'routine'} />
                    </div>
                    <div>
                      <div style={metaLabelStyle}>Suggested Department</div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>
                        {DEPT_LABELS[record.ai_suggested_department ?? 'general_medicine'] ??
                          record.ai_suggested_department}
                      </div>
                    </div>
                    {record.ai_confidence !== null && (
                      <div>
                        <div style={metaLabelStyle}>Confidence</div>
                        <div style={{ fontSize: 13, fontWeight: 500 }}>
                          {Math.round(record.ai_confidence * 100)}%
                        </div>
                      </div>
                    )}
                  </div>
                  {record.ai_reasoning && (
                    <div
                      style={{
                        fontSize: 12,
                        color: 'var(--color-text-secondary)',
                        fontStyle: 'italic',
                        paddingTop: 4,
                        borderTop: '1px solid var(--color-border)',
                        marginTop: 4,
                      }}
                    >
                      {record.ai_reasoning}
                    </div>
                  )}
                </div>
              </Section>
            )}

            {/* Final Decision */}
            <Section title="Final Decision">
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 12,
                  marginBottom: 12,
                }}
              >
                <div>
                  <div style={metaLabelStyle}>Urgency</div>
                  <UrgencyBadge urgency={record.final_urgency} />
                </div>
                <div>
                  <div style={metaLabelStyle}>Department</div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>
                    {DEPT_LABELS[record.final_department] ?? record.final_department}
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={metaLabelStyle}>Override Status</div>
                <OverrideStatusBadge label={overrideLabel} />
              </div>
            </Section>
          </div>
        ) : (
          <div
            style={{
              padding: '40px 24px',
              textAlign: 'center',
              color: 'var(--color-text-muted)',
              fontSize: 13,
            }}
          >
            Loading patient details...
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Section wrapper
// ---------------------------------------------------------------------------
function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          color: 'var(--color-text-muted)',
          marginBottom: 8,
        }}
      >
        {title}
      </div>
      {children}
    </div>
  )
}

const metaLabelStyle = {
  fontSize: 10,
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  color: 'var(--color-text-muted)',
  marginBottom: 2,
}

// ---------------------------------------------------------------------------
// Info grid helper
// ---------------------------------------------------------------------------
function InfoGrid({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '8px 16px',
      }}
    >
      {children}
    </div>
  )
}

function InfoItem({
  label,
  value,
  span,
}: {
  label: string
  value: string
  span?: boolean
}) {
  return (
    <div style={span ? { gridColumn: '1 / -1' } : {}}>
      <div style={metaLabelStyle}>{label}</div>
      <div style={{ fontSize: 13, color: 'var(--color-text)', fontWeight: 500 }}>
        {value}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// AllPatientsPage
// ---------------------------------------------------------------------------
export default function AllPatientsPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const selectedIdFromUrl = searchParams.get('id')

  // Filter state
  const [nameQuery, setNameQuery] = useState('')
  const [debouncedName, setDebouncedName] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [urgency, setUrgency] = useState('')
  const [department, setDepartment] = useState('')
  const [page, setPage] = useState(0)

  // Ref: has this page ever loaded (for empty state distinction)
  const hasEverLoaded = useRef(false)

  // Meta
  const { data: urgencyLevels = [] } = useMetaUrgencyLevels()
  const { data: departments = [] } = useMetaDepartments()

  // Fetch patient detail when URL has id
  const { data: selectedRecord } = useIntakeDetail(selectedIdFromUrl)

  // Build filters for API call
  const filters = {
    name: debouncedName || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    urgency: (urgency as IntakeOut['final_urgency']) || undefined,
    department: (department as IntakeOut['final_department']) || undefined,
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  }

  const { data, isLoading, isFetching } = useIntakeList(filters)

  if (!isLoading && data) {
    hasEverLoaded.current = true
  }

  const totalItems = data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE))
  const currentPage = Math.min(page + 1, totalPages)
  const hasFilters = Boolean(debouncedName || dateFrom || dateTo || urgency || department)
  const records = data?.items ?? []
  const isEmpty = !isLoading && records.length === 0

  // -------------------------------------------------------------------------
  // URL sync: modal open state driven by ?id= query param
  // -------------------------------------------------------------------------
  const isModalOpen = selectedIdFromUrl !== null

  function openPatient(id: string) {
    navigate(`/patients?id=${id}`)
  }

  function closeModal() {
    navigate('/patients')
  }

  // -------------------------------------------------------------------------
  // Debounce name search (300ms)
  // -------------------------------------------------------------------------
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedName(nameQuery)
      setPage(0)
    }, 300)
    return () => clearTimeout(timer)
  }, [nameQuery])

  // Reset page on filter changes (non-name)
  function handleFilterChange(setter: () => void) {
    setter()
    setPage(0)
  }

  // Clear all filters
  function clearFilters() {
    setNameQuery('')
    setDebouncedName('')
    setDateFrom('')
    setDateTo('')
    setUrgency('')
    setDepartment('')
    setPage(0)
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--color-surface-raised)',
        padding: '24px 32px',
        fontFamily: 'Inter, sans-serif',
      }}
    >
      {/* Patient Detail Modal (Phase 9) — driven by URL */}
      {isModalOpen && (
        <PatientDetailModal
          record={selectedRecord ?? null}
          onClose={closeModal}
        />
      )}

      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--color-text)', margin: 0 }}>
          All Patients
        </h1>
        <p style={{ fontSize: 13, color: 'var(--color-text-muted)', margin: '4px 0 0' }}>
          {totalItems > 0
            ? `${totalItems} registration${totalItems !== 1 ? 's' : ''} found`
            : 'Search and filter patient registrations'}
        </p>
      </div>

      {/* Filter Bar */}
      <div
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: '16px 20px',
          marginBottom: 16,
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr auto',
            gap: 12,
            alignItems: 'end',
          }}
        >
          {/* Name */}
          <div>
            <label style={labelStyle}>Name</label>
            <input
              type="text"
              value={nameQuery}
              onChange={(e) => setNameQuery(e.target.value)}
              placeholder="Search by name..."
              style={inputStyle}
            />
          </div>

          {/* Date from */}
          <div>
            <label style={labelStyle}>From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => handleFilterChange(() => setDateFrom(e.target.value))}
              style={inputStyle}
            />
          </div>

          {/* Date to */}
          <div>
            <label style={labelStyle}>To</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => handleFilterChange(() => setDateTo(e.target.value))}
              style={inputStyle}
            />
          </div>

          {/* Urgency */}
          <div>
            <label style={labelStyle}>Urgency</label>
            <select
              value={urgency}
              onChange={(e) => handleFilterChange(() => setUrgency(e.target.value))}
              style={inputStyle}
            >
              <option value="">All</option>
              {urgencyLevels.map((u) => (
                <option key={u} value={u}>
                  {URGENCY_LABELS[u] ?? u}
                </option>
              ))}
            </select>
          </div>

          {/* Department */}
          <div>
            <label style={labelStyle}>Department</label>
            <select
              value={department}
              onChange={(e) => handleFilterChange(() => setDepartment(e.target.value))}
              style={inputStyle}
            >
              <option value="">All</option>
              {departments.map((d) => (
                <option key={d} value={d}>
                  {DEPT_LABELS[d] ?? d}
                </option>
              ))}
            </select>
          </div>

          {/* Clear */}
          <button
            onClick={clearFilters}
            disabled={!hasFilters}
            style={{
              padding: '8px 14px',
              background: hasFilters ? 'var(--color-surface)' : 'var(--color-surface-raised)',
              color: hasFilters ? 'var(--color-text-secondary)' : 'var(--color-text-disabled)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              fontSize: 13,
              fontWeight: 500,
              cursor: hasFilters ? 'pointer' : 'not-allowed',
              whiteSpace: 'nowrap',
            }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Results Table */}
      <div
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-sm)',
          overflow: 'hidden',
        }}
      >
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr
                style={{
                  background: 'var(--color-surface-raised)',
                  borderBottom: '1px solid var(--color-border)',
                }}
              >
                {['Patient', 'Age', 'Gender', 'Urgency', 'Department', 'Source', 'Registered', ''].map(
                  (h) => (
                    <th key={h} style={thStyle}>
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
                : isEmpty
                ? null
                : records.map((record) => {
                    const source = computeSource(record)
                    const reg = new Date(record.created_at)
                    return (
                      <tr
                        key={record.id}
                        onClick={() => openPatient(record.id)}
                        style={{
                          cursor: 'pointer',
                          borderBottom: '1px solid var(--color-border)',
                        }}
                        onMouseEnter={(e) => {
                          ;(e.currentTarget as HTMLElement).style.background =
                            'var(--color-surface-raised)'
                        }}
                        onMouseLeave={(e) => {
                          ;(e.currentTarget as HTMLElement).style.background = ''
                        }}
                      >
                        <td style={tdStyle}>{record.patient.name}</td>
                        <td style={{ ...tdStyle, textAlign: 'center' }}>{record.patient.age}</td>
                        <td style={{ ...tdStyle, textAlign: 'center' }}>{record.patient.gender}</td>
                        <td style={{ ...tdStyle, textAlign: 'center' }}>
                          <UrgencyBadge urgency={record.final_urgency} />
                        </td>
                        <td style={tdStyle}>
                          {DEPT_LABELS[record.final_department] ?? record.final_department}
                        </td>
                        <td style={{ ...tdStyle, textAlign: 'center' }}>
                          <SourceBadge source={source} />
                        </td>
                        <td style={tdStyle}>
                          <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
                            {reg.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          </span>
                          <br />
                          <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                            {reg.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </td>
                        <td style={{ ...tdStyle, textAlign: 'center' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              openPatient(record.id)
                            }}
                            style={{
                              padding: '4px 10px',
                              background: 'var(--color-primary-bg)',
                              color: 'var(--color-primary)',
                              border: '1px solid var(--color-border)',
                              borderRadius: 'var(--radius-md)',
                              fontSize: 12,
                              fontWeight: 500,
                              cursor: 'pointer',
                            }}
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    )
                  })}
            </tbody>
          </table>
        </div>

        {/* Empty state */}
        {isEmpty && (
          <EmptyState hasFilters={hasFilters && hasEverLoaded.current} />
        )}

        {/* Pagination */}
        {!isEmpty && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 20px',
              borderTop: '1px solid var(--color-border)',
            }}
          >
            <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
              {totalItems === 0
                ? 'No results'
                : `${page * PAGE_SIZE + 1}–${Math.min((page + 1) * PAGE_SIZE, totalItems)} of ${totalItems}`}
            </span>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                Page {currentPage} of {totalPages}
              </span>

              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                style={pageBtnStyle}
              >
                ← Prev
              </button>

              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                style={pageBtnStyle}
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Style helpers
// ---------------------------------------------------------------------------
const labelStyle = {
  display: 'block',
  fontSize: 11,
  fontWeight: 600,
  color: 'var(--color-text-secondary)',
  marginBottom: 4,
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
}

const inputStyle = {
  width: '100%',
  padding: '7px 10px',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  fontSize: 13,
  color: 'var(--color-text)',
  background: 'var(--color-surface)',
  outline: 'none',
}

const thStyle = {
  padding: '8px 10px',
  fontSize: 11,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
  color: 'var(--color-text-muted)',
  textAlign: 'left',
  whiteSpace: 'nowrap',
}

const tdStyle = {
  padding: '10px 10px',
  fontSize: 13,
  color: 'var(--color-text)',
}

const pageBtnStyle = {
  padding: '5px 12px',
  background: 'var(--color-surface)',
  color: 'var(--color-text-secondary)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  fontSize: 12,
  fontWeight: 500,
  cursor: 'pointer',
}
