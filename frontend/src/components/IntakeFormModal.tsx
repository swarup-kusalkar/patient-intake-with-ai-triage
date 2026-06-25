/**
 * src/components/IntakeFormModal.tsx — Phase 6 Intake Form with AI Triage State Machine.
 *
 * Flow: Analyze (optional) → Review / Override → Save
 *
 * State machine (Section 7):
 * - aiSuggestion: latest AI suggestion from POST /triage/analyze (null = Analyze not called)
 * - finalUrgency / finalDepartment: pre-filled from AI suggestion, always editable
 * - isLowConfidence: true when AI confidence < 0.5
 *
 * Edge cases (Phase 6.4):
 * - Analyze clicked multiple times → each call overwrites aiSuggestion; snapshot is always latest
 * - Analyze never clicked → all ai_* fields sent as null, dropdowns empty
 * - Analyze fails (503) → aiSuggestion stays null, manual dropdowns shown, registration not blocked
 * - Modal close → all state cleared (form.reset() + local state reset)
 *
 * "Accept" is implicit: leaving the pre-filled dropdown untouched = acceptance.
 * No separate Accept button.
 */
import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

import type { TriageAnalyzeResponse } from '../api/types'
import { useTriageAnalyze, useCreateIntake, useMetaDepartments, useMetaUrgencyLevels } from '../api/hooks'
import { intakeFormSchema } from '../schemas/intake'
import TriageSuggestionPanel from './TriageSuggestionPanel'

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface IntakeFormModalProps {
  isOpen: boolean
  onClose: () => void
}

// ---------------------------------------------------------------------------
// Combined form schema — patient fields + urgency/department (both required)
// ---------------------------------------------------------------------------
const formSchema = intakeFormSchema.extend({
  final_urgency: z.string().min(1, 'Urgency is required'),
  final_department: z.string().min(1, 'Department is required'),
})

type FormValues = z.infer<typeof formSchema>

// ---------------------------------------------------------------------------
// Urgency / department display labels
// ---------------------------------------------------------------------------
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
// Toast notification
// ---------------------------------------------------------------------------
function Toast({
  message,
  type,
  onDismiss,
}: {
  message: string
  type: 'error' | 'success'
  onDismiss: () => void
}) {
  const isError = type === 'error'
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        padding: '10px 14px',
        background: isError ? 'var(--urgency-urgent-bg)' : 'var(--urgency-routine-bg)',
        border: `1px solid ${isError ? 'var(--urgency-urgent-border)' : 'var(--urgency-routine-border)'}`,
        borderRadius: 'var(--radius-md)',
        color: isError ? 'var(--urgency-urgent-text)' : 'var(--urgency-routine-text)',
        fontSize: 13,
        marginBottom: 16,
      }}
    >
      <span style={{ flex: 1 }}>{message}</span>
      <button
        onClick={onDismiss}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: 'inherit',
          fontSize: 16,
          lineHeight: 1,
          padding: 0,
          opacity: 0.7,
        }}
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Spinner
// ---------------------------------------------------------------------------
function Spinner() {
  return (
    <span
      style={{
        display: 'inline-block',
        width: 14,
        height: 14,
        border: '2px solid rgba(255,255,255,0.3)',
        borderTopColor: '#fff',
        borderRadius: '50%',
        animation: 'spin 0.6s linear infinite',
      }}
    />
  )
}

// ---------------------------------------------------------------------------
// Field wrapper
// ---------------------------------------------------------------------------
function FieldWrap({
  label,
  error,
  children,
}: {
  label: string
  error?: string
  children: ReactNode
}) {
  return (
    <div>
      <label style={labelStyle}>{label}</label>
      {children}
      {error && <ErrorMsg>{error}</ErrorMsg>}
    </div>
  )
}

// ---------------------------------------------------------------------------
// IntakeFormModal
// ---------------------------------------------------------------------------
export default function IntakeFormModal({ isOpen, onClose }: IntakeFormModalProps) {
  // React Query hooks
  const { data: departments = [] } = useMetaDepartments()
  const { data: urgencyLevels = [] } = useMetaUrgencyLevels()
  const analyzeMutation = useTriageAnalyze()
  const createMutation = useCreateIntake()

  // AI triage state
  const [aiSuggestion, setAiSuggestion] = useState<TriageAnalyzeResponse | null>(null)
  const [isLowConfidence, setIsLowConfidence] = useState(false)

  // Toast state
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' } | null>(null)

  // Form — all fields unified including final_urgency / final_department
  const {
    register,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    mode: 'onChange',
    defaultValues: {
      name: '',
      age: undefined,
      gender: '',
      contact_number: '',
      symptoms_text: '',
      final_urgency: '',
      final_department: '',
    },
  })

  const symptomsText = watch('symptoms_text') ?? ''
  const finalUrgency = watch('final_urgency')
  const finalDepartment = watch('final_department')

  // Watched patient fields for canSave
  const name = watch('name')
  const age = watch('age')
  const gender = watch('gender')
  const contact_number = watch('contact_number')

  const canSave =
    Boolean(name) &&
    age !== undefined &&
    age !== null &&
    Boolean(gender) &&
    Boolean(contact_number) &&
    symptomsText.length >= 10 &&
    Boolean(finalUrgency) &&
    Boolean(finalDepartment)

  // -------------------------------------------------------------------------
  // Analyze — POST /triage/analyze → pre-fill urgency/department
  // -------------------------------------------------------------------------
  async function handleAnalyze() {
    setToast(null)
    const symptoms = symptomsText.trim()
    if (symptoms.length < 10) return

    try {
      const result = await analyzeMutation.mutateAsync({ symptoms_text: symptoms })
      setAiSuggestion(result)
      setValue('final_urgency', result.urgency, { shouldValidate: true })
      setValue('final_department', result.department, { shouldValidate: true })
      setIsLowConfidence(result.confidence !== null && result.confidence < 0.5)
    } catch (err: unknown) {
      const apiErr = err as { status?: number }
      if (apiErr.status === 503) {
        setToast({
          message: 'AI service unavailable — please select urgency and department manually.',
          type: 'error',
        })
      } else {
        setToast({
          message: 'Analysis failed — please try again or select manually.',
          type: 'error',
        })
      }
      setAiSuggestion(null)
      setIsLowConfidence(false)
    }
  }

  // -------------------------------------------------------------------------
  // Save — builds full IntakeCreate payload including AI snapshot
  // -------------------------------------------------------------------------
  async function handleSave(formData: FormValues) {
    setToast(null)
    try {
      await createMutation.mutateAsync({
        name: formData.name,
        age: formData.age,
        gender: formData.gender,
        contact_number: formData.contact_number,
        symptoms_text: formData.symptoms_text,
        triage_source: aiSuggestion?.source ?? null,
        ai_suggested_urgency: aiSuggestion?.urgency ?? null,
        ai_suggested_department: aiSuggestion?.department ?? null,
        ai_confidence: aiSuggestion?.confidence ?? null,
        ai_reasoning: aiSuggestion?.reasoning ?? null,
        ai_raw_response: null,
        final_urgency: formData.final_urgency as 'routine' | 'priority' | 'urgent',
        final_department: formData.final_department as
          | 'general_medicine'
          | 'cardiology'
          | 'neurology'
          | 'orthopedics'
          | 'dermatology'
          | 'ent'
          | 'pulmonology'
          | 'gastroenterology'
          | 'emergency',
      })
      setToast({ message: 'Patient registered successfully.', type: 'success' })
      setTimeout(handleClose, 1200)
    } catch {
      setToast({
        message: 'Failed to save — please check all fields and try again.',
        type: 'error',
      })
    }
  }

  // -------------------------------------------------------------------------
  // Modal close — reset all state
  // -------------------------------------------------------------------------
  function handleClose() {
    reset()
    setAiSuggestion(null)
    setIsLowConfidence(false)
    setToast(null)
    onClose()
  }

  // -------------------------------------------------------------------------
  // Close on Escape key
  // -------------------------------------------------------------------------
  const modalRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') handleClose()
    }
    if (isOpen) document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [isOpen])

  if (!isOpen) return null

  const isAnalyzing = analyzeMutation.isPending
  const isSaving = createMutation.isPending

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
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose()
      }}
    >
      <div
        ref={modalRef}
        style={{
          background: 'var(--color-surface)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-xl)',
          width: '100%',
          maxWidth: 560,
          maxHeight: '90vh',
          overflowY: 'auto',
          margin: 16,
        }}
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
            padding: '20px 24px 0',
          }}
        >
          <h2
            id="modal-title"
            style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text)' }}
          >
            Register Patient
          </h2>
          <button
            onClick={handleClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: 22,
              color: 'var(--color-text-muted)',
              padding: 4,
              lineHeight: 1,
              borderRadius: 'var(--radius-sm)',
            }}
            aria-label="Close modal"
          >
            ×
          </button>
        </div>

        {/* Toast */}
        {toast && (
          <div style={{ padding: '16px 24px 0' }}>
            <Toast
              message={toast.message}
              type={toast.type}
              onDismiss={() => setToast(null)}
            />
          </div>
        )}

        {/* Form */}
        <form
          onSubmit={handleSubmit(handleSave)}
          noValidate
          style={{ padding: '16px 24px 24px' }}
        >
          {/* AI suggestion panel */}
          <TriageSuggestionPanel suggestion={aiSuggestion} />

          {/* Patient fields — row 1 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <FieldWrap label="Name *" error={errors.name?.message}>
              <Input
                {...register('name')}
                placeholder="Full name"
                hasError={Boolean(errors.name)}
              />
            </FieldWrap>
            <FieldWrap label="Age *" error={errors.age?.message}>
              <Input
                {...register('age', { valueAsNumber: true })}
                type="number"
                placeholder="Age"
                min={0}
                max={130}
                hasError={Boolean(errors.age)}
              />
            </FieldWrap>
          </div>

          {/* Patient fields — row 2 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <FieldWrap label="Gender *" error={errors.gender?.message}>
              <Input
                {...register('gender')}
                placeholder="M / F / Other"
                hasError={Boolean(errors.gender)}
              />
            </FieldWrap>
            <FieldWrap label="Contact Number *" error={errors.contact_number?.message}>
              <Input
                {...register('contact_number')}
                placeholder="Phone number"
                hasError={Boolean(errors.contact_number)}
              />
            </FieldWrap>
          </div>

          {/* Symptoms */}
          <div style={{ marginBottom: 16 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 6,
              }}
            >
              <label style={labelStyle}>Symptoms *</label>
              <span
                style={{
                  fontSize: 11,
                  color: symptomsText.length > 2000 ? 'var(--urgency-urgent)' : 'var(--color-text-muted)',
                }}
              >
                {symptomsText.length} / 2000
              </span>
            </div>
            <textarea
              {...register('symptoms_text')}
              rows={4}
              placeholder="Describe symptoms in detail (minimum 10 characters)..."
              maxLength={2000}
              style={{
                ...inputBaseStyle,
                resize: 'vertical',
                minHeight: 96,
                borderColor: errors.symptoms_text ? 'var(--urgency-urgent)' : 'var(--color-border)',
              }}
            />
            {errors.symptoms_text && <ErrorMsg>{errors.symptoms_text.message}</ErrorMsg>}
          </div>

          {/* Analyze button */}
          <div style={{ marginBottom: 16 }}>
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={isAnalyzing || symptomsText.length < 10}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 16px',
                background:
                  isAnalyzing || symptomsText.length < 10
                    ? 'var(--color-text-disabled)'
                    : 'var(--color-primary)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                fontSize: 14,
                fontWeight: 600,
                cursor: isAnalyzing || symptomsText.length < 10 ? 'not-allowed' : 'pointer',
                transition: 'background 0.15s',
              }}
            >
              {isAnalyzing ? <Spinner /> : null}
              {isAnalyzing ? 'Analyzing...' : 'Analyze Symptoms'}
            </button>
            <span
              style={{
                marginLeft: 12,
                fontSize: 12,
                color: 'var(--color-text-muted)',
                verticalAlign: 'middle',
              }}
            >
              {symptomsText.length < 10
                ? `Add ${10 - symptomsText.length} more character${
                    10 - symptomsText.length !== 1 ? 's' : ''
                  } to enable`
                : 'Optional — AI will suggest urgency and department'}
            </span>
          </div>

          {/* Low-confidence warning */}
          {isLowConfidence && (
            <div
              style={{
                fontSize: 12,
                color: 'var(--urgency-priority-text)',
                background: 'var(--urgency-priority-bg)',
                border: '1px solid var(--urgency-priority-border)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 10px',
                marginBottom: 16,
              }}
            >
              Low AI confidence — please review the urgency and department selections carefully.
            </div>
          )}

          {/* Final Urgency dropdown */}
          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>Final Urgency *</label>
            <select
              {...register('final_urgency')}
              style={{
                ...inputBaseStyle,
                cursor: 'pointer',
                borderColor: errors.final_urgency ? 'var(--urgency-urgent)' : 'var(--color-border)',
              }}
            >
              <option value="">Select urgency...</option>
              {urgencyLevels.map((u) => (
                <option key={u} value={u}>
                  {URGENCY_LABELS[u] ?? u}
                </option>
              ))}
            </select>
            {errors.final_urgency && <ErrorMsg>{errors.final_urgency.message}</ErrorMsg>}
          </div>

          {/* Final Department dropdown */}
          <div style={{ marginBottom: 24 }}>
            <label style={labelStyle}>Final Department *</label>
            <select
              {...register('final_department')}
              style={{
                ...inputBaseStyle,
                cursor: 'pointer',
                borderColor: errors.final_department ? 'var(--urgency-urgent)' : 'var(--color-border)',
              }}
            >
              <option value="">Select department...</option>
              {departments.map((d) => (
                <option key={d} value={d}>
                  {DEPT_LABELS[d] ?? d}
                </option>
              ))}
            </select>
            {errors.final_department && <ErrorMsg>{errors.final_department.message}</ErrorMsg>}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={handleClose}
              style={{
                padding: '9px 16px',
                background: 'transparent',
                color: 'var(--color-text-secondary)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                fontSize: 14,
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSave || isSaving}
              style={{
                padding: '9px 20px',
                background: canSave && !isSaving ? 'var(--color-primary)' : 'var(--color-text-disabled)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                fontSize: 14,
                fontWeight: 600,
                cursor: canSave && !isSaving ? 'pointer' : 'not-allowed',
                transition: 'background 0.15s',
              }}
            >
              {isSaving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Style helpers
// ---------------------------------------------------------------------------
const labelStyle = {
  display: 'block',
  fontSize: 13,
  fontWeight: 600,
  color: 'var(--color-text)',
  marginBottom: 4,
}

const inputBaseStyle = {
  width: '100%',
  padding: '8px 12px',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  fontSize: 14,
  color: 'var(--color-text)',
  background: 'var(--color-surface)',
  outline: 'none',
  transition: 'border-color 0.15s',
}

function Input({
  hasError,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { hasError?: boolean }) {
  return (
    <input
      {...props}
      style={{
        ...inputBaseStyle,
        borderColor: hasError ? 'var(--urgency-urgent)' : 'var(--color-border)',
      }}
    />
  )
}

function ErrorMsg({ children }: { children: ReactNode }) {
  return (
    <span
      style={{
        fontSize: 11,
        color: 'var(--urgency-urgent)',
        marginTop: 2,
        display: 'block',
      }}
    >
      {children}
    </span>
  )
}
