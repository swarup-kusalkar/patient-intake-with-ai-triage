/**
 * src/api/client.ts — Axios instance with error envelope interceptor.
 *
 * Design decisions:
 * - baseURL '/api/v1' — all requests are relative, no hardcoded host
 * - Response interceptor: parses {"error": {...}} envelope into a typed
 *   ApiRequestError class — every hook gets the same error shape
 *   regardless of which backend error path fired (ValidationError,
 *   HTTPException, or generic 500).
 */
import axios, { AxiosError } from 'axios'

// ---------------------------------------------------------------------------
// Typed API error — mirrors the backend's unified error envelope
// ---------------------------------------------------------------------------
export interface ApiErrorPayload {
  code: string
  message: string
  field: string | null
}

export class ApiRequestError extends Error {
  public readonly code: string
  public readonly field: string | null
  public readonly status: number

  constructor(payload: ApiErrorPayload, status: number) {
    super(payload.message)
    this.name = 'ApiRequestError'
    this.code = payload.code
    this.field = payload.field
    this.status = status
  }
}

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------
const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  timeout: 30_000, // 30s — accounts for slow LLM calls
})

// ---------------------------------------------------------------------------
// Response interceptor — normalize error shapes
//
// Backend always returns: {"error": {"code": "...", "message": "...", "field": "..."}}
// Transform this into ApiRequestError so hooks always catch the same type.
// ---------------------------------------------------------------------------
apiClient.interceptors.response.use(
  // Success path — pass through unchanged
  (response) => response,

  // Error path — parse error envelope
  (error: AxiosError<{ error: ApiErrorPayload }>) => {
    const status = error.response?.status ?? 0
    const errorPayload = error.response?.data?.error

    if (errorPayload) {
      // Backend returned a structured error envelope — use it
      throw new ApiRequestError(errorPayload, status)
    }

    // Network error, CORS, or timeout — no response body
    throw new ApiRequestError(
      {
        code: 'NETWORK_ERROR',
        message: error.message || 'Network error — please check your connection.',
        field: null,
      },
      status,
    )
  },
)

export default apiClient
