/**
 * src/schemas/intake.ts — Zod validation schemas for the intake form.
 *
 * Used with react-hook-form + @hookform/resolvers/zod for client-side
 * form validation. These are the client-side layer — Pydantic on the
 * backend is the actual source of truth (the client can always be bypassed).
 *
 * Validation rules mirror the backend constraints exactly:
 * - name: 1–120 chars
 * - age: integer 0–130
 * - gender: required (non-empty)
 * - contact_number: required (non-empty)
 * - symptoms_text: 10–2000 chars (minimum ensures meaningful analysis)
 *
 * The minimum on symptoms_text (10 chars) matches the backend's
 * TriageAnalyzeRequest minimum — prevents sending "ok" or "yes" to the AI.
 */
import { z } from 'zod'

// ---------------------------------------------------------------------------
// Patient fields schema
// ---------------------------------------------------------------------------
export const patientSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .max(120, 'Name must be 120 characters or fewer'),

  age: z
    .number({
      required_error: 'Age is required',
      invalid_type_error: 'Age must be a number',
    })
    .int('Age must be a whole number')
    .min(0, 'Age must be 0 or greater')
    .max(130, 'Age must be 130 or less'),

  gender: z
    .string()
    .min(1, 'Gender is required'),

  contact_number: z
    .string()
    .regex(/^\d{10}$/, 'Contact number must be exactly 10 digits'),
})

// ---------------------------------------------------------------------------
// Symptoms schema
// ---------------------------------------------------------------------------
export const symptomsSchema = z.object({
  symptoms_text: z
    .string()
    .min(10, 'Symptoms must be at least 10 characters for meaningful analysis')
    .max(2000, 'Symptoms must be 2000 characters or fewer'),
})

// ---------------------------------------------------------------------------
// Combined intake form schema (used by IntakeFormModal)
// ---------------------------------------------------------------------------
export const intakeFormSchema = patientSchema.merge(symptomsSchema)

// ---------------------------------------------------------------------------
// Inferred TypeScript types
// ---------------------------------------------------------------------------
export type PatientFormData = z.infer<typeof patientSchema>
export type SymptomsFormData = z.infer<typeof symptomsSchema>
export type IntakeFormData = z.infer<typeof intakeFormSchema>
