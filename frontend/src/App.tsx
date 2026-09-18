import {
  type FormEvent,
  useEffect,
  useMemo,
  useState,
} from 'react'

import './App.css'

import {
  API_BASE_URL,
  analyzePrompt,
  getHealth,
  getModels,
  multiRoutePrompt,
  routePrompt,
} from './api/client'

import type {
  HealthResponse,
  ModelInfo,
  ModelTier,
  MultiTaskExecutionResult,
  QueryAnalysis,
  RoutedResponse,
} from './api/types'


const navigation = [
  'Overview',
  'Route Prompt',
  'Multi-Task',
]


const fallbackModels: ModelInfo[] = [
  {
    tier: 'low',
    model_name: 'qwen3:1.7b',
    compute_score: 1,
  },
  {
    tier: 'medium',
    model_name: 'qwen3:4b',
    compute_score: 2,
  },
  {
    tier: 'high',
    model_name: 'qwen3:8b',
    compute_score: 4,
  },
]


function formatNumber(
  value: number | null | undefined,
  digits = 2,
) {
  if (value === null || value === undefined) {
    return '—'
  }

  return value.toFixed(digits)
}


function App() {
  const [health, setHealth] =
    useState<HealthResponse | null>(null)

  const [models, setModels] =
    useState<ModelInfo[]>(fallbackModels)

  const [loadingSystem, setLoadingSystem] =
    useState(true)

  const [systemError, setSystemError] =
    useState<string | null>(null)

  const [prompt, setPrompt] =
    useState(
      'Explain how database indexing improves query performance.',
    )

  const [overrideTier, setOverrideTier] =
    useState<ModelTier | ''>('')

  const [analysis, setAnalysis] =
    useState<QueryAnalysis | null>(null)

  const [routeResult, setRouteResult] =
    useState<RoutedResponse | null>(null)

  const [routing, setRouting] =
    useState(false)

  const [routingError, setRoutingError] =
    useState<string | null>(null)

  const [multiPrompt, setMultiPrompt] =
    useState(
      'Summarize why database indexes improve performance; extract the email alice@example.com; and explain when a full table scan may still be useful.',
    )

  const [multiResult, setMultiResult] =
    useState<MultiTaskExecutionResult | null>(null)

  const [multiRouting, setMultiRouting] =
    useState(false)

  const [multiError, setMultiError] =
    useState<string | null>(null)

  const [activeNavigation, setActiveNavigation] =
    useState('Overview')


  useEffect(() => {
    let cancelled = false

    async function loadSystemData() {
      try {
        setLoadingSystem(true)
        setSystemError(null)

        const [
          healthResult,
          modelResult,
        ] = await Promise.all([
          getHealth(),
          getModels(),
        ])

        if (cancelled) {
          return
        }

        setHealth(healthResult)
        setModels(modelResult)
      } catch (error) {
        if (cancelled) {
          return
        }

        setSystemError(
          error instanceof Error
            ? error.message
            : 'Unable to reach AURA backend.',
        )
      } finally {
        if (!cancelled) {
          setLoadingSystem(false)
        }
      }
    }

    void loadSystemData()

    return () => {
      cancelled = true
    }
  }, [])


  const backendHealthy =
    health?.status === 'healthy'


  const normalizedModels =
    useMemo(() => {
      return [...models].sort(
        (left, right) =>
          left.compute_score -
          right.compute_score,
      )
    }, [models])


  async function handleRoute(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    const cleanPrompt =
      prompt.trim()

    if (!cleanPrompt) {
      setRoutingError(
        'Enter a prompt before routing.',
      )
      return
    }

    try {
      setRouting(true)
      setRoutingError(null)
      setAnalysis(null)
      setRouteResult(null)

      const analysisResult =
        await analyzePrompt({
          prompt: cleanPrompt,
        })

      setAnalysis(analysisResult)

      const routed =
        await routePrompt({
          prompt: cleanPrompt,
          override_tier:
            overrideTier || null,
        })

      setRouteResult(routed)
    } catch (error) {
      setRoutingError(
        error instanceof Error
          ? error.message
          : 'AURA routing failed.',
      )
    } finally {
      setRouting(false)
    }
  }


  function handleNavigation(
    item: string,
  ) {
    const targets: Record<string, string> = {
      Overview: 'overview',
      'Route Prompt': 'route-prompt',
      'Multi-Task': 'multi-task',
    }

    const targetId =
      targets[item]

    let element =
      targetId
        ? document.getElementById(
            targetId,
          )
        : null

    if (!element) {
      return
    }

    setActiveNavigation(item)

    element.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    })
  }


  async function handleMultiRoute(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    const cleanPrompt =
      multiPrompt.trim()

    if (!cleanPrompt) {
      setMultiError(
        'Enter a multi-task prompt before routing.',
      )
      return
    }

    try {
      setMultiRouting(true)
      setMultiError(null)
      setMultiResult(null)

      const result =
        await multiRoutePrompt({
          prompt: cleanPrompt,
        })

      setMultiResult(result)
    } catch (error) {
      setMultiError(
        error instanceof Error
          ? error.message
          : 'AURA multi-task routing failed.',
      )
    } finally {
      setMultiRouting(false)
    }
  }


  const selectedTier =
    routeResult?.routing.selected_tier

  const confidence =
    routeResult?.confidence

  const analytics =
    routeResult?.analytics

  const privacy =
    routeResult?.privacy

  const privacyPolicy =
    routeResult?.privacy_policy

  const escalation =
    routeResult?.escalation


  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            A
          </div>

          <div>
            <strong>
              AURA
            </strong>

            <span>
              LLM Router
            </span>
          </div>
        </div>

        <nav
          className="nav-list"
          aria-label="Primary navigation"
        >
          {navigation.map(
            (item) => (
              <button
                aria-current={
                  activeNavigation === item
                    ? 'page'
                    : undefined
                }
                className={
                  activeNavigation === item
                    ? 'nav-item active'
                    : 'nav-item'
                }
                key={item}
                onClick={() =>
                  handleNavigation(item)
                }
                type="button"
              >
                <span className="nav-dot" />
                {item}
              </button>
            ),
          )}
        </nav>

        <div className="sidebar-status">
          <span
            className={
              backendHealthy
                ? 'status-dot online'
                : 'status-dot offline'
            }
          />

          <div>
            <strong>
              Local AI Stack
            </strong>

            <span>
              {loadingSystem
                ? 'Checking...'
                : backendHealthy
                  ? 'Backend ready'
                  : 'Backend offline'}
            </span>
          </div>
        </div>
      </aside>


      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              Adaptive Unified Routing Architecture
            </p>

            <h1>
              Intelligent LLM Routing
            </h1>
          </div>

          <div className="topbar-actions">
            <span className="version-badge">
              API {API_BASE_URL}
            </span>

            <span className="health-badge">
              <span
                className={
                  backendHealthy
                    ? 'status-dot online'
                    : 'status-dot offline'
                }
              />

              {loadingSystem
                ? 'Checking system'
                : backendHealthy
                  ? 'System healthy'
                  : 'System unavailable'}
            </span>
          </div>
        </header>


        {systemError && (
          <div
            className="system-alert"
            role="alert"
          >
            <strong>
              Backend connection unavailable.
            </strong>

            <span>
              {systemError}
            </span>
          </div>
        )}


        <section
          className="metric-grid"
          aria-label="System overview"
          id="overview"
        >
          <article className="metric-card">
            <span className="metric-label">
              Routing Engine
            </span>

            <strong>
              Adaptive
            </strong>

            <small>
              History-aware model selection
            </small>
          </article>

          <article className="metric-card">
            <span className="metric-label">
              Model Tiers
            </span>

            <strong>
              {loadingSystem
                ? '...'
                : `${models.length} Local`}
            </strong>

            <small>
              Loaded from /models
            </small>
          </article>

          <article className="metric-card">
            <span className="metric-label">
              Backend
            </span>

            <strong>
              {loadingSystem
                ? 'Checking'
                : backendHealthy
                  ? 'Healthy'
                  : 'Offline'}
            </strong>

            <small>
              {health?.service ??
                'aura-backend'}
            </small>
          </article>

          <article className="metric-card">
            <span className="metric-label">
              Last Route
            </span>

            <strong>
              {selectedTier
                ? selectedTier.toUpperCase()
                : '—'}
            </strong>

            <small>
              {routeResult?.routing.selected_model ??
                'No route yet'}
            </small>
          </article>
        </section>


        <section className="content-grid">
          <article
            className="panel routing-panel"
            id="route-prompt"
          >
            <div className="panel-header">
              <div>
                <p className="eyebrow">
                  Routing Playground
                </p>

                <h2>
                  Route a prompt
                </h2>
              </div>

              <span className="panel-tag">
                Live /analysis + /route
              </span>
            </div>


            <form
              onSubmit={handleRoute}
            >
              <label
                className="prompt-label"
                htmlFor="prompt"
              >
                Prompt
              </label>

              <textarea
                id="prompt"
                onChange={(event) =>
                  setPrompt(
                    event.target.value,
                  )
                }
                placeholder="Enter a prompt for AURA..."
                rows={6}
                value={prompt}
              />


              <div className="routing-controls">
                <label className="control">
                  <span>
                    Tier override
                  </span>

                  <select
                    onChange={(event) =>
                      setOverrideTier(
                        event.target.value as
                          | ModelTier
                          | '',
                      )
                    }
                    value={overrideTier}
                  >
                    <option value="">
                      Automatic
                    </option>

                    <option value="low">
                      LOW
                    </option>

                    <option value="medium">
                      MEDIUM
                    </option>

                    <option value="high">
                      HIGH
                    </option>
                  </select>
                </label>


                <div className="control">
                  <span>
                    Analyzer recommendation
                  </span>

                  <strong>
                    {analysis
                      ? analysis.recommended_tier.toUpperCase()
                      : 'Waiting'}
                  </strong>
                </div>


                <button
                  className="primary-button"
                  disabled={routing}
                  type="submit"
                >
                  {routing
                    ? 'Routing...'
                    : 'Route Prompt'}

                  <span aria-hidden="true">
                    →
                  </span>
                </button>
              </div>
            </form>


            {routingError && (
              <div
                className="route-error"
                role="alert"
              >
                {routingError}
              </div>
            )}


            {analysis && (
              <div className="analysis-strip">
                <div>
                  <span>
                    Task
                  </span>

                  <strong>
                    {analysis.task_type}
                  </strong>
                </div>

                <div>
                  <span>
                    Complexity
                  </span>

                  <strong>
                    {analysis.complexity_score}/10
                  </strong>
                </div>

                <div>
                  <span>
                    Reasoning
                  </span>

                  <strong>
                    {analysis.reasoning_required
                      ? 'Required'
                      : 'Not required'}
                  </strong>
                </div>

                <div>
                  <span>
                    Words
                  </span>

                  <strong>
                    {analysis.features.word_count}
                  </strong>
                </div>
              </div>
            )}


            {!routeResult && (
              <div className="routing-preview">
                <div className="route-node">
                  <span>01</span>

                  <div>
                    <small>
                      Analyze
                    </small>

                    <strong>
                      Complexity & task type
                    </strong>
                  </div>
                </div>

                <div className="route-line" />

                <div className="route-node">
                  <span>02</span>

                  <div>
                    <small>
                      Select
                    </small>

                    <strong>
                      Best eligible model
                    </strong>
                  </div>
                </div>

                <div className="route-line" />

                <div className="route-node">
                  <span>03</span>

                  <div>
                    <small>
                      Evaluate
                    </small>

                    <strong>
                      Confidence & escalation
                    </strong>
                  </div>
                </div>
              </div>
            )}


            {routeResult && (
              <div className="result-stack">
                <section className="result-response">
                  <span>
                    Model Response
                  </span>

                  <p>
                    {routeResult.response}
                  </p>
                </section>


                <div className="result-summary-grid">
                  <div>
                    <span>
                      Selected tier
                    </span>

                    <strong>
                      {routeResult.routing.selected_tier.toUpperCase()}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Model
                    </span>

                    <strong>
                      {routeResult.routing.selected_model}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Confidence
                    </span>

                    <strong>
                      {confidence
                        ? `${Math.round(
                            confidence.score * 100,
                          )}%`
                        : '—'}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Escalated
                    </span>

                    <strong>
                      {escalation?.escalated
                        ? 'Yes'
                        : 'No'}
                    </strong>
                  </div>
                </div>
              </div>
            )}
          </article>


          <article className="panel model-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">
                  Local Models
                </p>

                <h2>
                  Model tiers
                </h2>
              </div>

              <span
                className={
                  backendHealthy
                    ? 'status-dot online'
                    : 'status-dot offline'
                }
              />
            </div>

            <div className="tier-list">
              {normalizedModels.map(
                (item) => (
                  <div
                    className="tier-row"
                    key={
                      `${item.tier}-${item.model_name}`
                    }
                  >
                    <div
                      className={
                        `tier-icon ${item.tier}`
                      }
                    >
                      {item.tier
                        .slice(0, 1)
                        .toUpperCase()}
                    </div>

                    <div className="tier-copy">
                      <strong>
                        {item.tier.toUpperCase()}
                      </strong>

                      <span>
                        {item.model_name}
                      </span>

                      <small>
                        {item.description ??
                          'Local Ollama model'}
                      </small>
                    </div>

                    <div className="compute-badge">
                      {item.compute_score}×
                    </div>
                  </div>
                ),
              )}
            </div>
          </article>
        </section>


        {routeResult && (
          <section className="result-grid">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">
                    Explainability
                  </p>

                  <h2>
                    Routing decision
                  </h2>
                </div>
              </div>

              <div className="detail-list">
                <div>
                  <span>
                    Summary
                  </span>

                  <p>
                    {
                      routeResult.routing.explanation
                        .summary
                    }
                  </p>
                </div>

                <div>
                  <span>
                    Selection
                  </span>

                  <p>
                    {
                      routeResult.routing.explanation
                        .selection_reason
                    }
                  </p>
                </div>

                <div>
                  <span>
                    Compute tradeoff
                  </span>

                  <p>
                    {
                      routeResult.routing.explanation
                        .compute_quality_tradeoff
                    }
                  </p>
                </div>
              </div>
            </article>


            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">
                    Privacy
                  </p>

                  <h2>
                    Data protection
                  </h2>
                </div>
              </div>

              <div className="result-summary-grid compact">
                <div>
                  <span>
                    Risk
                  </span>

                  <strong>
                    {privacy?.risk_level ??
                      'none'}
                  </strong>
                </div>

                <div>
                  <span>
                    Sensitive
                  </span>

                  <strong>
                    {privacy?.contains_sensitive_data
                      ? 'Yes'
                      : 'No'}
                  </strong>
                </div>

                <div>
                  <span>
                    Local required
                  </span>

                  <strong>
                    {privacy?.requires_local
                      ? 'Yes'
                      : 'No'}
                  </strong>
                </div>

                <div>
                  <span>
                    Scope
                  </span>

                  <strong>
                    {privacyPolicy?.execution_scope ??
                      'local'}
                  </strong>
                </div>
              </div>

              {privacy?.categories.length ? (
                <div className="chip-list">
                  {privacy.categories.map(
                    (category) => (
                      <span key={category}>
                        {category}
                      </span>
                    ),
                  )}
                </div>
              ) : null}
            </article>


            <article
              className="panel"
              id="analytics"
            >
              <div className="panel-header">
                <div>
                  <p className="eyebrow">
                    Analytics
                  </p>

                  <h2>
                    Route metrics
                  </h2>
                </div>
              </div>

              <div className="result-summary-grid compact">
                <div>
                  <span>
                    Attempts
                  </span>

                  <strong>
                    {analytics?.attempt_count ??
                      '—'}
                  </strong>
                </div>

                <div>
                  <span>
                    Tokens
                  </span>

                  <strong>
                    {analytics?.total_tokens ??
                      '—'}
                  </strong>
                </div>

                <div>
                  <span>
                    Latency
                  </span>

                  <strong>
                    {analytics
                      ? `${formatNumber(
                          analytics.total_latency_seconds,
                        )}s`
                      : '—'}
                  </strong>
                </div>

                <div>
                  <span>
                    Compute
                  </span>

                  <strong>
                    {analytics
                      ? formatNumber(
                          analytics.normalized_compute_cost,
                        )
                      : '—'}
                  </strong>
                </div>
              </div>
            </article>
          </section>
        )}


        <section
          className="panel multi-task-panel"
          id="multi-task"
        >
          <div className="panel-header">
            <div>
              <p className="eyebrow">
                Multi-Task Routing
              </p>

              <h2>
                Decompose and route multiple tasks
              </h2>
            </div>

            <span className="panel-tag">
              Live /multi-route
            </span>
          </div>


          <form
            className="multi-task-form"
            onSubmit={handleMultiRoute}
          >
            <label
              className="prompt-label"
              htmlFor="multi-prompt"
            >
              Multi-task prompt
            </label>

            <textarea
              id="multi-prompt"
              onChange={(event) =>
                setMultiPrompt(
                  event.target.value,
                )
              }
              placeholder="Enter multiple independent tasks..."
              rows={5}
              value={multiPrompt}
            />

            <div className="multi-task-actions">
              <div>
                <strong>
                  Independent task routing
                </strong>

                <span>
                  Each task receives its own model,
                  confidence, privacy policy, and analytics.
                </span>
              </div>

              <button
                className="primary-button"
                disabled={multiRouting}
                type="submit"
              >
                {multiRouting
                  ? 'Routing tasks...'
                  : 'Route Multi-Task'}

                <span aria-hidden="true">
                  ?
                </span>
              </button>
            </div>
          </form>


          {multiError && (
            <div
              className="route-error"
              role="alert"
            >
              {multiError}
            </div>
          )}


          {multiResult && (
            <div className="multi-task-results">
              <div className="multi-overview-grid">
                <div>
                  <span>
                    Multi-task
                  </span>

                  <strong>
                    {multiResult.is_multi_task
                      ? 'Detected'
                      : 'Single task'}
                  </strong>
                </div>

                <div>
                  <span>
                    Tasks
                  </span>

                  <strong>
                    {multiResult.task_count}
                  </strong>
                </div>

                <div>
                  <span>
                    Total attempts
                  </span>

                  <strong>
                    {
                      multiResult.analytics
                        .total_attempt_count
                    }
                  </strong>
                </div>

                <div>
                  <span>
                    Total tokens
                  </span>

                  <strong>
                    {multiResult.analytics.total_tokens}
                  </strong>
                </div>

                <div>
                  <span>
                    Latency
                  </span>

                  <strong>
                    {formatNumber(
                      multiResult.analytics
                        .total_latency_seconds,
                    )}s
                  </strong>
                </div>

                <div>
                  <span>
                    Compute
                  </span>

                  <strong>
                    {formatNumber(
                      multiResult.analytics
                        .normalized_compute_cost,
                    )}
                  </strong>
                </div>
              </div>


              <section className="aggregated-response">
                <span>
                  Aggregated Response
                </span>

                <p>
                  {multiResult.aggregated_response}
                </p>
              </section>


              <div className="subtask-grid">
                {multiResult.tasks.map(
                  (task) => (
                    <article
                      className="subtask-card"
                      key={task.index}
                    >
                      <div className="subtask-header">
                        <div>
                          <span>
                            Task {task.index}
                          </span>

                          <strong>
                            {task.task_type}
                          </strong>
                        </div>

                        <span
                          className={
                            `tier-pill ${task.selected_tier}`
                          }
                        >
                          {task.selected_tier.toUpperCase()}
                        </span>
                      </div>


                      <p className="subtask-text">
                        {task.task}
                      </p>


                      <div className="subtask-response">
                        {task.response}
                      </div>


                      <div className="subtask-metrics">
                        <div>
                          <span>
                            Model
                          </span>

                          <strong>
                            {task.selected_model}
                          </strong>
                        </div>

                        <div>
                          <span>
                            Confidence
                          </span>

                          <strong>
                            {Math.round(
                              task.confidence.score * 100,
                            )}%
                          </strong>
                        </div>

                        <div>
                          <span>
                            Escalated
                          </span>

                          <strong>
                            {task.escalation.escalated
                              ? 'Yes'
                              : 'No'}
                          </strong>
                        </div>

                        <div>
                          <span>
                            Privacy
                          </span>

                          <strong>
                            {task.privacy.risk_level}
                          </strong>
                        </div>

                        <div>
                          <span>
                            Tokens
                          </span>

                          <strong>
                            {task.analytics.total_tokens}
                          </strong>
                        </div>

                        <div>
                          <span>
                            Latency
                          </span>

                          <strong>
                            {formatNumber(
                              task.analytics
                                .total_latency_seconds,
                            )}s
                          </strong>
                        </div>

                        <div>
                          <span>
                            Compute
                          </span>

                          <strong>
                            {formatNumber(
                              task.analytics
                                .normalized_compute_cost,
                            )}
                          </strong>
                        </div>

                        <div>
                          <span>
                            Scope
                          </span>

                          <strong>
                            {
                              task.privacy_policy
                                .execution_scope
                            }
                          </strong>
                        </div>
                      </div>


                      {task.escalation.attempts.length > 1 && (
                        <div className="attempt-path">
                          <span>
                            Escalation path
                          </span>

                          <div>
                            {task.escalation.attempts.map(
                              (
                                attempt,
                                attemptIndex,
                              ) => (
                                <span
                                  key={
                                    `${task.index}-${attemptIndex}-${attempt.tier}`
                                  }
                                >
                                  {attempt.tier.toUpperCase()}
                                  {' ? '}
                                  {Math.round(
                                    attempt.confidence_score *
                                      100,
                                  )}
                                  %
                                </span>
                              ),
                            )}
                          </div>
                        </div>
                      )}
                    </article>
                  ),
                )}
              </div>
            </div>
          )}
        </section>


        <section className="bottom-grid">
          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">
                  Decision Pipeline
                </p>

                <h2>
                  Why AURA routes intelligently
                </h2>
              </div>
            </div>

            <div className="feature-grid">
              <div className="feature">
                <span>01</span>
                <strong>
                  Query Analysis
                </strong>
                <p>
                  Classifies task type,
                  complexity, and reasoning needs.
                </p>
              </div>

              <div className="feature">
                <span>02</span>
                <strong>
                  Privacy Policy
                </strong>
                <p>
                  Ensures sensitive workloads stay
                  on local models.
                </p>
              </div>

              <div className="feature">
                <span>03</span>
                <strong>
                  Confidence
                </strong>
                <p>
                  Escalates when lower tiers do not
                  meet quality needs.
                </p>
              </div>

              <div className="feature">
                <span>04</span>
                <strong>
                  Adaptive Learning
                </strong>
                <p>
                  Uses reliability history to
                  improve future routing.
                </p>
              </div>
            </div>
          </article>


          <article className="panel activity-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">
                  System
                </p>

                <h2>
                  Architecture status
                </h2>
              </div>
            </div>

            <div className="status-list">
              <div>
                <span
                  className={
                    backendHealthy
                      ? 'status-dot online'
                      : 'status-dot offline'
                  }
                />

                <p>
                  <strong>
                    Backend API
                  </strong>

                  <small>
                    {backendHealthy
                      ? 'Connected'
                      : 'Unavailable'}
                  </small>
                </p>
              </div>

              <div>
                <span className="status-dot online" />

                <p>
                  <strong>
                    Privacy Engine
                  </strong>

                  <small>
                    Enforced
                  </small>
                </p>
              </div>

              <div>
                <span className="status-dot online" />

                <p>
                  <strong>
                    Learning Store
                  </strong>

                  <small>
                    Persistent
                  </small>
                </p>
              </div>

              <div>
                <span className="status-dot online" />

                <p>
                  <strong>
                    Analytics
                  </strong>

                  <small>
                    Enabled
                  </small>
                </p>
              </div>
            </div>
          </article>
        </section>
      </main>
    </div>
  )
}


export default App
