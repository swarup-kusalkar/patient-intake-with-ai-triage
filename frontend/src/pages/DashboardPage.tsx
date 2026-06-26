/**
 * src/pages/DashboardPage.tsx — Phase 7 Dashboard Page.
 *
 * Sections:
 * 7.1  Stat Cards Row — total, routine/priority/urgent with color-coded counts
 * 7.2  Charts — urgency doughnut + department horizontal bar (Recharts)
 * 7.3  Today's Mini-Table — latest 5 registrations with source column
 * 7.4  Register Patient Button → IntakeFormModal
 *
 * Data sources:
 *   - useDashboardSummary(date) → GET /api/v1/dashboard/summary
 *   - useIntakeList({ date_from, date_to, limit: 5 }) → GET /api/v1/intake
 *
 * Source column (Section 7.3):
 *   triage_source = null          → "Manual"
 *   urgency_overridden = false AND department_overridden = false → "AI accepted"
 *   Either override flag true                                      → "Overridden"
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

import { useDashboardSummary, useIntakeList } from '../api/hooks'
import { type IntakeOut } from '../api/types'
import IntakeFormModal from '../components/IntakeFormModal'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const TODAY = new Date().toISOString().split('T')[0]

const URGENCY_COLORS = {
  routine: 'var(--urgency-routine)',
  priority: 'var(--urgency-priority)',
  urgent: 'var(--urgency-urgent)',
}

const DEPT_COLORS = [
  '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b',
  '#10b981', '#6366f1', '#14b8a6', '#f97316', '#ef4444',
]

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

// ---------------------------------------------------------------------------
// Source computation (Section 7.3 spec)
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
// Stat Card
// ---------------------------------------------------------------------------
function StatCard({
  label,
  count,
  color,
  bg,
}: {
  label: string
  count: number
  color: string
  bg: string
}) {
  return (
    <div
      style={{
        flex: 1,
        minWidth: 120,
        padding: '16px 20px',
        background: bg,
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-sm)',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
      }}
    >
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: 'var(--color-text-muted)',
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 36,
          fontWeight: 800,
          color,
          lineHeight: 1,
        }}
      >
        {count}
      </div>
    </div>
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
        border: `1px solid ${
          isManual ? 'var(--color-border)' : isOverridden ? 'var(--urgency-priority-border)' : 'var(--urgency-routine-border)'
        }`,
      }}
    >
      {source}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Mini Table Row
// ---------------------------------------------------------------------------
function MiniTableRow({ record }: { record: IntakeOut }) {
  const source = computeSource(record)
  const time = new Date(record.created_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <tr
      style={{
        borderBottom: '1px solid var(--color-border)',
        background: 'var(--color-surface)',
      }}
    >
      <td style={tdStyle}>{record.patient.name}</td>
      <td style={{ ...tdStyle, textAlign: 'center' }}>{record.patient.age}</td>
      <td style={{ ...tdStyle, textAlign: 'center' }}>
        <UrgencyBadge urgency={record.final_urgency} />
      </td>
      <td style={{ ...tdStyle }}>
        {DEPT_LABELS[record.final_department] ?? record.final_department}
      </td>
      <td style={{ ...tdStyle, textAlign: 'center' }}>
        <SourceBadge source={source} />
      </td>
      <td style={{ ...tdStyle, textAlign: 'right', color: 'var(--color-text-muted)' }}>
        {time}
      </td>
    </tr>
  )
}

const tdStyle = {
  padding: '10px 12px',
  fontSize: 13,
  color: 'var(--color-text)',
}

// ---------------------------------------------------------------------------
// Loading Skeleton
// ---------------------------------------------------------------------------
function SkeletonBox({ height = 200 }: { height?: number }) {
  return (
    <div
      style={{
        height,
        borderRadius: 'var(--radius-lg)',
        background: 'linear-gradient(90deg, var(--color-border) 25%, var(--color-surface-raised) 50%, var(--color-border) 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.4s ease-in-out infinite',
      }}
    />
  )
}

// ---------------------------------------------------------------------------
// Dashboard Page
// ---------------------------------------------------------------------------
export default function DashboardPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)

  const {
    data: summary,
    isLoading: summaryLoading,
  } = useDashboardSummary(TODAY)

  const {
    data: recentRecords,
    isLoading: recordsLoading,
  } = useIntakeList({
    date_from: TODAY,
    date_to: TODAY,
    limit: 5,
  })

  const isLoading = summaryLoading || recordsLoading

  const total = summary?.total ?? 0
  const byUrgency = summary?.by_urgency ?? { routine: 0, priority: 0, urgent: 0 }
  const byDepartment = summary?.by_department ?? {}

  // Recharts data: only include departments with count > 0
  const deptData = Object.entries(byDepartment)
    .filter(([, count]) => count > 0)
    .map(([name, count]) => ({
      name: DEPT_LABELS[name] ?? name,
      fullName: name,
      count,
    }))

  const urgencyData = [
    { name: 'Routine', value: byUrgency.routine, color: URGENCY_COLORS.routine },
    { name: 'Priority', value: byUrgency.priority, color: URGENCY_COLORS.priority },
    { name: 'Urgent', value: byUrgency.urgent, color: URGENCY_COLORS.urgent },
  ]

  const hasData = total > 0

  return (
    <>
      <IntakeFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />

      <div
        style={{
          minHeight: '100vh',
          background: 'var(--color-surface-raised)',
          padding: '24px 32px',
          fontFamily: 'Inter, sans-serif',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 24,
          }}
        >
          <div>
            <h1
              style={{
                fontSize: 22,
                fontWeight: 800,
                color: 'var(--color-text)',
                margin: 0,
              }}
            >
              Dashboard
            </h1>
            <p
              style={{
                fontSize: 13,
                color: 'var(--color-text-muted)',
                margin: '4px 0 0',
              }}
            >
              {new Date().toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 20px',
              background: 'var(--color-primary)',
              color: '#fff',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: 'var(--shadow-md)',
              transition: 'background 0.15s',
            }}
          >
            + Register Patient
          </button>
        </div>

        {/* Stat Cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 16,
            marginBottom: 24,
          }}
        >
          {isLoading ? (
            <>
              <SkeletonBox height={80} />
              <SkeletonBox height={80} />
              <SkeletonBox height={80} />
              <SkeletonBox height={80} />
            </>
          ) : (
            <>
              <StatCard label="Total Today" count={total} color="var(--color-text)" bg="var(--color-surface)" />
              <StatCard
                label="Routine"
                count={byUrgency.routine}
                color="var(--urgency-routine)"
                bg="var(--urgency-routine-bg)"
              />
              <StatCard
                label="Priority"
                count={byUrgency.priority}
                color="var(--urgency-priority)"
                bg="var(--urgency-priority-bg)"
              />
              <StatCard
                label="Urgent"
                count={byUrgency.urgent}
                color="var(--urgency-urgent)"
                bg="var(--urgency-urgent-bg)"
              />
            </>
          )}
        </div>

        {/* Charts Row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 2fr',
            gap: 16,
            marginBottom: 24,
          }}
        >
          {/* Urgency Doughnut */}
          <div
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '20px',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: 'var(--color-text)',
                marginBottom: 16,
              }}
            >
              Urgency Breakdown
            </div>
            {isLoading ? (
              <SkeletonBox height={180} />
            ) : hasData ? (
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={urgencyData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={48}
                    outerRadius={72}
                    paddingAngle={3}
                  >
                    {urgencyData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => [value, '']}
                    contentStyle={{
                      fontSize: 12,
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      boxShadow: 'var(--shadow-sm)',
                    }}
                  />
                  <Legend
                    formatter={(value: string) => (
                      <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
                        {value}
                      </span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart label="No data yet" />
            )}
          </div>

          {/* Department Bar Chart */}
          <div
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '20px',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: 'var(--color-text)',
                marginBottom: 16,
              }}
            >
              Department Breakdown
            </div>
            {isLoading ? (
              <SkeletonBox height={180} />
            ) : deptData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart
                  data={deptData}
                  layout="vertical"
                  margin={{ left: 0, right: 16 }}
                >
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fontSize: 11 }}
                    width={100}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(value: number) => [value, 'Registrations']}
                    contentStyle={{
                      fontSize: 12,
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      boxShadow: 'var(--shadow-sm)',
                    }}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {deptData.map((_, i) => (
                      <Cell key={i} fill={DEPT_COLORS[i % DEPT_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart label="No data yet" />
            )}
          </div>
        </div>

        {/* Today's Mini-Table */}
        <div
          style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-sm)',
            overflow: 'hidden',
          }}
        >
          {/* Table header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '16px 20px',
              borderBottom: '1px solid var(--color-border)',
            }}
          >
            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: 'var(--color-text)',
              }}
            >
              Today's Registrations
            </div>
            <Link
              to="/patients"
              style={{
                fontSize: 13,
                color: 'var(--color-primary)',
                textDecoration: 'none',
                fontWeight: 500,
              }}
            >
              View all →
            </Link>
          </div>

          {isLoading ? (
            <div style={{ padding: 20, textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 13 }}>
              Loading...
            </div>
          ) : !recentRecords?.items.length ? (
            <div
              style={{
                padding: '32px 20px',
                textAlign: 'center',
                color: 'var(--color-text-muted)',
                fontSize: 13,
              }}
            >
              No patients registered today
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr
                    style={{
                      background: 'var(--color-surface-raised)',
                      borderBottom: '1px solid var(--color-border)',
                    }}
                  >
                    {['Patient', 'Age', 'Urgency', 'Department', 'Source', 'Time'].map((h) => (
                      <th
                        key={h}
                        style={{
                          padding: '8px 12px',
                          fontSize: 11,
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          letterSpacing: '0.04em',
                          color: 'var(--color-text-muted)',
                          textAlign: h === 'Age' || h === 'Urgency' || h === 'Source' || h === 'Time'
                            ? 'center'
                            : h === 'Patient'
                            ? 'left'
                            : 'left',
                        }}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {recentRecords.items.map((record) => (
                    <MiniTableRow key={record.id} record={record} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Override rate note */}
        {summary?.override_rate !== null && summary?.override_rate !== undefined && (
          <div
            style={{
              marginTop: 12,
              fontSize: 12,
              color: 'var(--color-text-muted)',
              textAlign: 'right',
            }}
          >
            AI override rate:{' '}
            <strong style={{ color: 'var(--color-text-secondary)' }}>
              {Math.round(summary.override_rate * 100)}%
            </strong>{' '}
            of AI-assisted registrations
          </div>
        )}
      </div>
    </>
  )
}

// ---------------------------------------------------------------------------
// Empty chart placeholder
// ---------------------------------------------------------------------------
function EmptyChart({ label }: { label: string }) {
  return (
    <div
      style={{
        height: 180,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--color-text-muted)',
        fontSize: 13,
      }}
    >
      {label}
    </div>
  )
}
