/**
 * src/api/types.ts — TypeScript interfaces mirroring backend Pydantic schemas.
 *
 * These types are the contract between the frontend and the API.
 * They mirror the backend schemas exactly — any mismatch here means
 * a runtime error that TypeScript catches at compile time.
 *
 * Source of truth for enum values: backend GET /api/v1/meta/* endpoints.
 * The string union types here are for static typing; runtime validation
 * uses the values fetched from the API.
 */

// ---------------------------------------------------------------------------
// Enum string types — match backend Python enum values exactly
// ---------------------------------------------------------------------------

export type UrgencyLevel = 'routine' | 'priority' | 'urgent'

export type Department =
  | 'general_medicine'
  | 'cardiology'
  | 'neurology'
  | 'orthopedics'
  | 'dermatology'
  | 'ent'
  | 'pulmonology'
  | 'gastroenterology'
  | 'emergency'

export type TriageSource = 'rule_engine' | 'llm' | 'manual'

// ---------------------------------------------------------------------------
// Triage analyze
// ---------------------------------------------------------------------------

export interface TriageAnalyzeRequest {
  symptoms_text: string
}

export interface TriageAnalyzeResponse {
  source: TriageSource
  urgency: UrgencyLevel
  department: Department
  confidence: number | null
  reasoning: string | null
}

// ---------------------------------------------------------------------------
// Patient
// ---------------------------------------------------------------------------

export interface PatientOut {
  id: string
  name: string
  age: number
  gender: string
  contact_number: string
  created_at: string
}

// ---------------------------------------------------------------------------
// Intake
// ---------------------------------------------------------------------------

export interface IntakeCreate {
  // Patient fields
  name: string
  age: number
  gender: string
  contact_number: string
  symptoms_text: string

  // AI snapshot — null when Analyze was never clicked
  triage_source: TriageSource | null
  ai_suggested_urgency: UrgencyLevel | null
  ai_suggested_department: Department | null
  ai_confidence: number | null
  ai_reasoning: string | null
  ai_raw_response: Record<string, unknown> | null

  // Final confirmed values — always required
  final_urgency: UrgencyLevel
  final_department: Department
}

export interface IntakeOut {
  id: string
  patient_id: string
  symptoms_text: string
  triage_source: TriageSource | null
  ai_suggested_urgency: UrgencyLevel | null
  ai_suggested_department: Department | null
  ai_confidence: number | null
  ai_reasoning: string | null
  ai_raw_response: Record<string, unknown> | null
  final_urgency: UrgencyLevel
  final_department: Department
  urgency_overridden: boolean | null
  department_overridden: boolean | null
  created_at: string
}

export interface IntakeListResponse {
  items: IntakeOut[]
  total: number
  page: number
  page_size: number
}

// ---------------------------------------------------------------------------
// Intake list filters — used by the All Patients page and dashboard mini-table
// ---------------------------------------------------------------------------

export interface IntakeListFilters {
  name?: string
  date_from?: string   // ISO date string YYYY-MM-DD
  date_to?: string     // ISO date string YYYY-MM-DD
  urgency?: UrgencyLevel
  department?: Department
  limit?: number       // default 20
  offset?: number      // default 0
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export interface DashboardSummary {
  date: string
  total: number
  by_urgency: { routine: number; priority: number; urgent: number }
  by_department: {
    general_medicine: number
    cardiology: number
    neurology: number
    orthopedics: number
    dermatology: number
    ent: number
    pulmonology: number
    gastroenterology: number
    emergency: number
  }
  override_rate: number | null
}

// ---------------------------------------------------------------------------
// Meta
// ---------------------------------------------------------------------------

export interface MetaResponse {
  departments: Department[]
  urgency_levels: UrgencyLevel[]
}
