export type ModelTier = 'low' | 'medium' | 'high'


export type HealthResponse = {
  status: string
  service: string
}


export type ModelInfo = {
  tier: ModelTier
  model_name: string
  compute_score: number
  description?: string
}


export type ModelsResponse =
  | ModelInfo[]
  | {
      models: ModelInfo[]
    }


export type QueryFeatures = {
  word_count: number
  has_code: boolean
  has_reasoning_markers: boolean
  has_multiple_requirements: boolean
}


export type QueryAnalysis = {
  task_type: string
  complexity_score: number
  reasoning_required: boolean
  recommended_tier: string
  explanation: string
  features: QueryFeatures
}


export type AnalyzeRequest = {
  prompt: string
}


export type RoutingExplanation = {
  summary: string
  selection_reason: string
  complexity_reason: string
  reasoning_reason: string
  compute_quality_tradeoff: string
  override_reason: string
  signals: string[]
}


export type RoutingDecision = {
  recommended_tier: string
  selected_tier: string
  selected_model: string
  compute_score: number
  override_applied: boolean
  thinking_override_applied: boolean
  thinking_enabled: boolean
  analysis: QueryAnalysis
  explanation: RoutingExplanation
}


export type ConfidenceEvaluation = {
  score: number
  level: string
  should_escalate: boolean
  reasons: string[]
  response_word_count: number
}


export type EscalationAttempt = {
  tier: string
  model_name: string
  confidence_score: number
  confidence_level: string
  should_escalate: boolean
  reasons: string[]
}


export type EscalationSummary = {
  escalated: boolean
  initial_tier: string
  final_tier: string
  reason: string
  attempts: EscalationAttempt[]
}


export type PrivacyAssessment = {
  contains_sensitive_data: boolean
  risk_level: string
  requires_local: boolean
  categories: string[]
  signals: string[]
}


export type PrivacyRoutingPolicy = {
  privacy_enforced: boolean
  execution_scope: string
  external_routing_allowed: boolean
  selected_model_is_local: boolean
  reason: string
}


export type AttemptMetrics = {
  tier: string
  model_name: string
  compute_score: number
  confidence_score: number
  confidence_level: string
  should_escalate: boolean
  prompt_tokens: number
  output_tokens: number
  total_tokens: number
  latency_seconds: number
  tokens_per_second: number | null
  normalized_compute_cost: number
}


export type RouteAnalytics = {
  attempt_count: number
  total_prompt_tokens: number
  total_output_tokens: number
  total_tokens: number
  total_latency_seconds: number
  normalized_compute_cost: number
  final_attempt_compute_cost: number
  escalation_overhead_compute: number
  attempts: AttemptMetrics[]
}


export type RouteRequest = {
  prompt: string
  override_tier?: ModelTier | null
  override_thinking?: boolean | null
}


export type RoutedResponse = {
  prompt: string
  routing: RoutingDecision
  response: string
  confidence: ConfidenceEvaluation | null
  escalation: EscalationSummary | null
  privacy: PrivacyAssessment | null
  privacy_policy: PrivacyRoutingPolicy | null
  analytics: RouteAnalytics | null
  prompt_tokens: number | null
  output_tokens: number | null
  latency_seconds: number | null
  tokens_per_second: number | null
}


export type ApiErrorPayload = {
  detail?: string
}

export type MultiRouteRequest = {
  prompt: string
}


export type MultiTaskAnalytics = {
  task_count: number
  total_attempt_count: number
  total_prompt_tokens: number
  total_output_tokens: number
  total_tokens: number
  total_latency_seconds: number
  normalized_compute_cost: number
  final_attempt_compute_cost: number
  escalation_overhead_compute: number
}


export type SubtaskExecutionResult = {
  index: number
  task: string
  task_type: string
  recommended_tier: string
  selected_tier: string
  selected_model: string
  compute_score: number
  thinking_enabled: boolean
  response: string
  confidence: ConfidenceEvaluation
  escalation: EscalationSummary
  privacy: PrivacyAssessment
  privacy_policy: PrivacyRoutingPolicy
  analytics: RouteAnalytics
  prompt_tokens?: number | null
  output_tokens?: number | null
  latency_seconds?: number | null
  tokens_per_second?: number | null
}


export type MultiTaskExecutionResult = {
  original_prompt: string
  is_multi_task: boolean
  task_count: number
  tasks: SubtaskExecutionResult[]
  privacy: PrivacyAssessment
  analytics: MultiTaskAnalytics
  aggregated_response: string
  total_prompt_tokens: number
  total_output_tokens: number
  total_latency_seconds: number
  total_compute_score: number
}

export type PerformanceStats = {
  task_type: string
  tier: string
  attempts: number
  successes: number
  failures: number
  average_confidence: number
  average_latency_seconds: number
  average_normalized_compute_cost: number
  reliability_score: number
}


export type LearningHistory = Record<
  string,
  PerformanceStats
>


export type TierReliability = {
  tier: string
  attempts: number
  reliability_score: number
}


export type LearningRecommendation = {
  task_type: string
  baseline_tier: string
  recommended_tier: string
  learning_applied: boolean
  reason: string
  candidates: TierReliability[]
}
