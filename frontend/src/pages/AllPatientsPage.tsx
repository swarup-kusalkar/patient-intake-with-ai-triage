/**
 * src/pages/AllPatientsPage.tsx — Phase 8 All Patients Page.
 *
 * Features (Phase 8):
 * 8.1  Filter Bar — name (debounced 300ms), date range, urgency/department dropdowns, clear
 * 8.2  Results Table — Patient, Age, Gender, Urgency (badge), Department, Source, Time, Actions
 * 8.2  Pagination — prev/next + page indicator, 20 per page
 * 8.3  Empty States — no results for filters vs no patients at all
 *
 * Phase 9 (PatientDetailModal) is wired here: clicking View opens the modal.
 * The modal is currently a placeholder — URL sync is implemented separately.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { type IntakeOut } from '../api/types'
import {
  useIntakeList,
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
// Source computation (same logic as DashboardPage)
// ---------------------------------------------------------------------------
function computeSource(record: IntakeOut): string {
  if (record.triage_source === null) return 'Manual'
  if (!record.urgency_overridden && !record.department_overridden) return 'AI accepted'
  return 'Overridden'
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
              background: 'linear-gradient(90deg, var(--color-border) 25%, var(--color-surface-raised) 50%, var(--color-border) 75%)',
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
// AllPatientsPage
// ---------------------------------------------------------------------------
export default function AllPatientsPage() {
  // Filter state
  const [nameQuery, setNameQuery] = useState('')
  const [debouncedName, setDebouncedName] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [urgency, setUrgency] = useState<string>('')
  const [department, setDepartment] = useState<string>('')

  // Pagination (0-indexed offset internally)
  const [page, setPage] = useState(0)

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  // Ref to track if this is the "no patients at all" empty state
  const hasEverLoaded = useRef(false)

  // Meta
  const { data: urgencyLevels = [] } = useMetaUrgencyLevels()
  const { data: departments = [] } = useMetaDepartments()

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

  const hasFilters = Boolean(
    debouncedName || dateFrom || dateTo || urgency || department
  )

  const totalItems = data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE))
  const currentPage = Math.min(page + 1, totalPages)

  // -------------------------------------------------------------------------
  // Debounce name search (300ms)
  // -------------------------------------------------------------------------
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedName(nameQuery)
      setPage(0) // reset to first page on filter change
    }, 300)
    return () => clearTimeout(timer)
  }, [nameQuery])

  // Reset page when other filters change
  const handleFilterChange = useCallback((setter: () => void) => {
    setter()
    setPage(0)
  }, [])

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

  // Open patient detail modal
  function openPatient(id: string) {
    setSelectedId(id)
    setIsModalOpen(true)
  }

  function closeModal() {
    setIsModalOpen(false)
    setSelectedId(null)
  }

  const records = data?.items ?? []
  const hasRecords = records.length > 0
  const isEmpty = !isLoading && !hasRecords

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--color-surface-raised)',
        padding: '24px 32px',
        fontFamily: 'Inter, sans-serif',
      }}
    >
      {/* Patient Detail Modal placeholder (Phase 9) */}
      {isModalOpen && selectedId && (
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
          onClick={closeModal}
        >
          <div
            style={{
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-xl)',
              boxShadow: 'var(--shadow-xl)',
              width: '100%',
              maxWidth: 560,
              maxHeight: '90vh',
              overflowY: 'auto',
              margin: 16,
              padding: 24,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 16,
              }}
            >
              <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
                Patient Detail
              </h2>
              <button
                onClick={closeModal}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 22,
                  color: 'var(--color-text-muted)',
                  padding: 4,
                }}
              >
                ×
              </button>
            </div>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
              Patient ID: <code style={{ fontSize: 12 }}>{selectedId}</code>
            </div>
            <p
              style={{
                marginTop: 12,
                color: 'var(--color-text-muted)',
                fontSize: 12,
              }}
            >
              Full patient detail modal with AI suggestion display, override
              status, and registered at timestamp — Phase 9.
            </p>
          </div>
        </div>
      )}

      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <h1
          style={{
            fontSize: 22,
            fontWeight: 800,
            color: 'var(--color-text)',
            margin: 0,
          }}
        >
          All Patients
        </h1>
        <p
          style={{
            fontSize: 13,
            color: 'var(--color-text-muted)',
            margin: '4px 0 0',
          }}
        >
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
          {/* Name search */}
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

          {/* Urgency filter */}
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

          {/* Department filter */}
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
                {[
                  'Patient',
                  'Age',
                  'Gender',
                  'Urgency',
                  'Department',
                  'Source',
                  'Registered',
                  '',
                ].map((h) => (
                  <th
                    key={h}
                    style={thStyle}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array.from({ length: 5 }).map((_, i) => (
                    <SkeletonRow key={i} />
                  ))
                : isEmpty
                ? null
                : records.map((record) => {
                    const source = computeSource(record)
                    const registeredDate = new Date(record.created_at)
                    const dateStr = registeredDate.toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })
                    const timeStr = registeredDate.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })

                    return (
                      <tr
                        key={record.id}
                        onClick={() => openPatient(record.id)}
                        style={{
                          cursor: 'pointer',
                          borderBottom: '1px solid var(--color-border)',
                          transition: 'background 0.1s',
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
                        <td style={{ ...tdStyle, textAlign: 'center' }}>
                          {record.patient.age}
                        </td>
                        <td style={{ ...tdStyle, textAlign: 'center' }}>
                          {record.patient.gender}
                        </td>
                        <td style={{ ...tdStyle, textAlign: 'center' }}>
                          <UrgencyBadge urgency={record.final_urgency} />
                        </td>
                        <td style={tdStyle}>
                          {DEPT_LABELS[record.final_department] ??
                            record.final_department}
                        </td>
                        <td style={{ ...tdStyle, textAlign: 'center' }}>
                          <SourceBadge source={source} />
                        </td>
                        <td style={tdStyle}>
                          <div>
                            <span style={{ color: 'var(--color-text-secondary)', fontSize: 12 }}>
                              {dateStr}
                            </span>
                            <br />
                            <span style={{ color: 'var(--color-text-muted)', fontSize: 11 }}>
                              {timeStr}
                            </span>
                          </div>
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
        {isEmpty && <EmptyState hasFilters={hasFilters && hasEverLoaded.current} />}

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
            <span
              style={{
                fontSize: 12,
                color: 'var(--color-text-muted)',
              }}
            >
              {totalItems === 0
                ? 'No results'
                : `${page * PAGE_SIZE + 1}–${Math.min((page + 1) * PAGE_SIZE, totalItems)} of ${totalItems}`}
            </span>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span
                style={{
                  fontSize: 12,
                  color: 'var(--color-text-muted)',
                }}
              >
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
