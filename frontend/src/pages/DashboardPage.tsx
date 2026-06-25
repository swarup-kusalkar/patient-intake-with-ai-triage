/**
 * DashboardPage — Phase 0 placeholder.
 *
 * Full implementation in Phase 7:
 * - Stat cards row (total/routine/priority/urgent today)
 * - Urgency doughnut chart (Recharts)
 * - Department horizontal bar chart (Recharts)
 * - Today's mini-table (latest 5-10 registrations)
 * - Register Patient button → IntakeFormModal
 */
export default function DashboardPage() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      gap: '16px',
      fontFamily: 'Inter, sans-serif',
      backgroundColor: 'var(--color-surface-raised)',
    }}>
      <div style={{
        background: 'var(--color-surface)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-lg)',
        padding: '48px 64px',
        textAlign: 'center',
        maxWidth: '480px',
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🏥</div>
        <h1 style={{
          fontSize: '24px',
          fontWeight: '700',
          color: 'var(--color-text)',
          marginBottom: '8px',
        }}>
          Patient Intake System
        </h1>
        <p style={{
          color: 'var(--color-text-muted)',
          fontSize: '14px',
          marginBottom: '24px',
        }}>
          Dashboard — Phase 0 Placeholder
        </p>
        <div style={{
          display: 'inline-block',
          padding: '6px 16px',
          borderRadius: 'var(--radius-full)',
          background: 'var(--color-primary-bg)',
          color: 'var(--color-primary)',
          fontSize: '12px',
          fontWeight: '600',
        }}>
          ✓ Frontend is running
        </div>
        <div style={{ marginTop: '24px', borderTop: '1px solid var(--color-border)', paddingTop: '24px' }}>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
            Full dashboard UI in Phase 7 →
          </p>
          <a
            href="/patients"
            style={{
              color: 'var(--color-primary)',
              fontSize: '13px',
              textDecoration: 'none',
              marginTop: '8px',
              display: 'inline-block',
            }}
          >
            Go to All Patients →
          </a>
        </div>
      </div>
    </div>
  )
}
