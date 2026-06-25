/**
 * src/api/hooks.ts — React Query hooks for all API endpoints.
 *
 * Phase 0: All hooks are wired and return loading/error state correctly.
 * They will return data once the backend endpoints are implemented in
 * Phases 2–4.
 *
 * Design decisions:
 * - Centralized queryKeys object for consistent cache invalidation
 * - useCreateIntake invalidates both intake list and dashboard on success
 *   (one save → both the patient list and dashboard counts auto-refresh)
 * - useMetaDepartments / useMetaUrgencyLevels: staleTime=Infinity since
 *   enum values never change at runtime
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { UseQueryResult, UseMutationResult } from '@tanstack/react-query'

import apiClient from './client'
import type {
  TriageAnalyzeRequest,
  TriageAnalyzeResponse,
  IntakeCreate,
  IntakeOut,
  IntakeListResponse,
  IntakeListFilters,
  DashboardSummary,
  Department,
  UrgencyLevel,
} from './types'

// ---------------------------------------------------------------------------
// Centralized query key registry
// Consistent keys ensure correct cache invalidation across all hooks.
// ---------------------------------------------------------------------------
export const queryKeys = {
  meta: {
    departments: ['meta', 'departments'] as const,
    urgencyLevels: ['meta', 'urgency-levels'] as const,
  },
  intake: {
    all: ['intake'] as const,
    list: (filters: IntakeListFilters) => ['intake', 'list', filters] as const,
    detail: (id: string) => ['intake', 'detail', id] as const,
  },
  dashboard: {
    summary: (date: string) => ['dashboard', 'summary', date] as const,
  },
}

// ---------------------------------------------------------------------------
// Meta hooks — static data, never stale
// ---------------------------------------------------------------------------

export function useMetaDepartments(): UseQueryResult<Department[]> {
  return useQuery({
    queryKey: queryKeys.meta.departments,
    queryFn: async () => {
      const { data } = await apiClient.get<Department[]>('/meta/departments')
      return data
    },
    staleTime: Infinity,  // Enum values never change at runtime
  })
}

export function useMetaUrgencyLevels(): UseQueryResult<UrgencyLevel[]> {
  return useQuery({
    queryKey: queryKeys.meta.urgencyLevels,
    queryFn: async () => {
      const { data } = await apiClient.get<UrgencyLevel[]>('/meta/urgency-levels')
      return data
    },
    staleTime: Infinity,
  })
}

// ---------------------------------------------------------------------------
// Triage hook — mutation (POST, no cache entry)
// ---------------------------------------------------------------------------

export function useTriageAnalyze(): UseMutationResult<
  TriageAnalyzeResponse,
  Error,
  TriageAnalyzeRequest
> {
  return useMutation({
    mutationFn: async (request: TriageAnalyzeRequest) => {
      const { data } = await apiClient.post<TriageAnalyzeResponse>(
        '/triage/analyze',
        request,
      )
      return data
    },
  })
}

// ---------------------------------------------------------------------------
// Intake hooks
// ---------------------------------------------------------------------------

export function useIntakeList(
  filters: IntakeListFilters = {},
): UseQueryResult<IntakeListResponse> {
  return useQuery({
    queryKey: queryKeys.intake.list(filters),
    queryFn: async () => {
      const { data } = await apiClient.get<IntakeListResponse>('/intake', {
        params: filters,
      })
      return data
    },
  })
}

export function useIntakeDetail(id: string | null): UseQueryResult<IntakeOut> {
  return useQuery({
    queryKey: queryKeys.intake.detail(id ?? ''),
    queryFn: async () => {
      const { data } = await apiClient.get<IntakeOut>(`/intake/${id}`)
      return data
    },
    // Only fetch when we have an actual ID (modal is open)
    enabled: Boolean(id),
  })
}

export function useCreateIntake(): UseMutationResult<
  IntakeOut,
  Error,
  IntakeCreate
> {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (intake: IntakeCreate) => {
      const { data } = await apiClient.post<IntakeOut>('/intake', intake)
      return data
    },
    onSuccess: () => {
      // Invalidate both lists so they refetch with the new record
      queryClient.invalidateQueries({ queryKey: queryKeys.intake.all })
      // Invalidate today's dashboard — counts change after a new registration
      const today = new Date().toISOString().split('T')[0]
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.summary(today) })
    },
  })
}

// ---------------------------------------------------------------------------
// Dashboard hook
// ---------------------------------------------------------------------------

export function useDashboardSummary(
  date: string = new Date().toISOString().split('T')[0],
): UseQueryResult<DashboardSummary> {
  return useQuery({
    queryKey: queryKeys.dashboard.summary(date),
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardSummary>(
        '/dashboard/summary',
        { params: { date } },
      )
      return data
    },
    // Refetch every 60s so the dashboard stays current during a busy shift
    refetchInterval: 60_000,
  })
}
