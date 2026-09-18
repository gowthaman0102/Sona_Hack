import type {
  AnalyzeRequest,
  ApiErrorPayload,
  HealthResponse,
  LearningHistory,
  LearningRecommendation,
  ModelInfo,
  ModelsResponse,
  ModelTier,
  MultiRouteRequest,
  MultiTaskExecutionResult,
  PerformanceStats,
  QueryAnalysis,
  RouteRequest,
  RoutedResponse,
} from './types'


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  'http://127.0.0.1:8000'


async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
    },
  )

  if (!response.ok) {
    let message =
      `Request failed with status ${response.status}`

    try {
      const payload =
        (await response.json()) as ApiErrorPayload

      if (payload.detail) {
        message = payload.detail
      }
    } catch {
      // Preserve generic HTTP error.
    }

    throw new Error(message)
  }

  return response.json() as Promise<T>
}


export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>(
    '/health',
  )
}


export async function getModels(): Promise<ModelInfo[]> {
  const payload =
    await request<ModelsResponse>(
      '/models',
    )

  if (Array.isArray(payload)) {
    return payload
  }

  return payload.models
}


export async function analyzePrompt(
  payload: AnalyzeRequest,
): Promise<QueryAnalysis> {
  return request<QueryAnalysis>(
    '/analysis',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  )
}


export async function routePrompt(
  payload: RouteRequest,
): Promise<RoutedResponse> {
  return request<RoutedResponse>(
    '/route',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  )
}


export async function multiRoutePrompt(
  payload: MultiRouteRequest,
): Promise<MultiTaskExecutionResult> {
  return request<MultiTaskExecutionResult>(
    '/multi-route',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  )
}


export async function getLearningHistory(): Promise<LearningHistory> {
  return request<LearningHistory>(
    '/learning/history',
  )
}


export async function getTaskLearningHistory(
  taskType: string,
): Promise<PerformanceStats[]> {
  return request<PerformanceStats[]>(
    `/learning/history/${encodeURIComponent(taskType)}`,
  )
}


export async function getLearningRecommendation(
  taskType: string,
  baselineTier: ModelTier,
): Promise<LearningRecommendation> {
  const query = new URLSearchParams({
    baseline_tier: baselineTier,
  })

  return request<LearningRecommendation>(
    `/learning/recommendation/${encodeURIComponent(
      taskType,
    )}?${query.toString()}`,
  )
}


export {
  API_BASE_URL,
}
