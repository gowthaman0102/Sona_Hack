import type {
  AnalyzeRequest,
  ApiErrorPayload,
  HealthResponse,
  ModelInfo,
  ModelsResponse,
  MultiRouteRequest,
  MultiTaskExecutionResult,
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


export {
  API_BASE_URL,
}
