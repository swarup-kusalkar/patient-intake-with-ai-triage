/**
 * AllPatientsPage — Phase 0 placeholder.
 *
 * Full implementation in Phase 8:
 * - Filter bar (name search debounced 300ms, date range, urgency, department)
 * - Paginated results table (20 per page)
 * - Source column (AI accepted / Overridden / Manual)
 * - Click row → opens PatientDetailModal + URL updates to /patients?id=<uuid>
 *
 * Phase 9:
 * - PatientDetailModal — URL-synced via ?id=<uuid> query param
 */
import { Link } from 'react-router-dom'

export default function AllPatientsPage() {
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
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
        <h1 style={{
          fontSize: '24px',
          fontWeight: '700',
          color: 'var(--color-text)',
          marginBottom: '8px',
        }}>
          All Patients
        </h1>
        <p style={{
          color: 'var(--color-text-muted)',
          fontSize: '14px',
          marginBottom: '24px',
        }}>
          Patient Search & Audit — Phase 0 Placeholder
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
          ✓ Route /patients is registered
        </div>
        <div style={{ marginTop: '24px', borderTop: '1px solid var(--color-border)', paddingTop: '24px' }}>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
            Full table with filters and pagination in Phase 8 →
          </p>
          <Link
            to="/"
            style={{
              color: 'var(--color-primary)',
              fontSize: '13px',
              textDecoration: 'none',
              marginTop: '8px',
              display: 'inline-block',
            }}
          >
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}
