import {
  type FormEvent,
  useState,
} from 'react'

import {
  analyzePrompt,
  routePrompt,
} from '../api/client'
import { useAuraSession } from '../context/useAuraSession'
import type { ModelTier } from '../api/types'


function formatNumber(
  value: number | null | undefined,
  digits = 2,
) {
  if (value === null || value === undefined) {
    return '—'
  }

  return value.toFixed(digits)
}


export default function RoutePromptPage() {
  const {
    analysis,
    overrideTier,
    prompt,
    routeResult,
    setAnalysis,
    setOverrideTier,
    setPrompt,
    setRouteResult,
  } = useAuraSession()
  const [routing, setRouting] = useState(false)
  const [routingStage, setRoutingStage] =
    useState<'analyzing' | 'generating'>('analyzing')
  const [routingError, setRoutingError] =
    useState<string | null>(null)

  async function handleRoute(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    const cleanPrompt = prompt.trim()

    if (!cleanPrompt) {
      setRoutingError('Enter a prompt before routing.')
      return
    }

    try {
      setRouting(true)
      setRoutingStage('analyzing')
      setRoutingError(null)
      setAnalysis(null)
      setRouteResult(null)

      const analysisResult = await analyzePrompt({
        prompt: cleanPrompt,
      })
      setAnalysis(analysisResult)

      setRoutingStage('generating')
      const routed = await routePrompt({
        prompt: cleanPrompt,
        override_tier: overrideTier || null,
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

  const confidence = routeResult?.confidence
  const analytics = routeResult?.analytics
  const privacy = routeResult?.privacy
  const privacyPolicy = routeResult?.privacy_policy
  const escalation = routeResult?.escalation

  return (
    <>
      <section className="content-grid single-page-grid">
        <article className="panel routing-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Routing Playground</p>
              <h2>Route a prompt</h2>
            </div>
            <span className="panel-tag">Live /analysis + /route</span>
          </div>

          <form onSubmit={handleRoute}>
            <label className="prompt-label" htmlFor="prompt">
              Prompt
            </label>
            <textarea
              id="prompt"
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Enter a prompt for AURA..."
              rows={6}
              value={prompt}
            />

            <div className="routing-controls">
              <label className="control">
                <span>Tier override</span>
                <select
                  onChange={(event) =>
                    setOverrideTier(
                      event.target.value as ModelTier | '',
                    )
                  }
                  value={overrideTier}
                >
                  <option value="">Automatic</option>
                  <option value="low">LOW</option>
                  <option value="medium">MEDIUM</option>
                  <option value="high">HIGH</option>
                </select>
              </label>

              <div className="control">
                <span>Analyzer recommendation</span>
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
                  ? routingStage === 'analyzing'
                    ? 'Analyzing...'
                    : 'Generating...'
                  : 'Route Prompt'}
                <span aria-hidden="true">→</span>
              </button>
            </div>
          </form>

          {routing && (
            <div
              aria-live="polite"
              className="route-loading"
              role="status"
            >
              <span className="loading-spinner" aria-hidden="true" />
              <span>
                {routingStage === 'analyzing'
                  ? 'Analyzing prompt...'
                  : 'Generating response...'}
              </span>
            </div>
          )}

          {routingError && (
            <div className="route-error" role="alert">
              {routingError}
            </div>
          )}

          {analysis && (
            <div className="analysis-strip">
              <div>
                <span>Task</span>
                <strong>{analysis.task_type}</strong>
              </div>
              <div>
                <span>Complexity</span>
                <strong>{analysis.complexity_score}/10</strong>
              </div>
              <div>
                <span>Reasoning</span>
                <strong>
                  {analysis.reasoning_required
                    ? 'Required'
                    : 'Not required'}
                </strong>
              </div>
              <div>
                <span>Words</span>
                <strong>{analysis.features.word_count}</strong>
              </div>
            </div>
          )}

          {!routeResult && (
            <div className="routing-preview">
              <div className="route-node">
                <span>01</span>
                <div>
                  <small>Analyze</small>
                  <strong>Complexity &amp; task type</strong>
                </div>
              </div>
              <div className="route-line" />
              <div className="route-node">
                <span>02</span>
                <div>
                  <small>Select</small>
                  <strong>Best eligible model</strong>
                </div>
              </div>
              <div className="route-line" />
              <div className="route-node">
                <span>03</span>
                <div>
                  <small>Evaluate</small>
                  <strong>Confidence &amp; escalation</strong>
                </div>
              </div>
            </div>
          )}

          {routeResult && (
            <div className="result-stack">
              <section className="result-response">
                <span>Model Response</span>
                <p>{routeResult.response}</p>
              </section>

              <div className="result-summary-grid">
                <div>
                  <span>Selected tier</span>
                  <strong>
                    {routeResult.routing.selected_tier.toUpperCase()}
                  </strong>
                </div>
                <div>
                  <span>Model</span>
                  <strong>{routeResult.routing.selected_model}</strong>
                </div>
                <div>
                  <span>Confidence</span>
                  <strong>
                    {confidence
                      ? `${Math.round(confidence.score * 100)}%`
                      : '—'}
                  </strong>
                </div>
                <div>
                  <span>Escalated</span>
                  <strong>{escalation?.escalated ? 'Yes' : 'No'}</strong>
                </div>
              </div>
            </div>
          )}
        </article>
      </section>

      {routeResult && (
        <section className="result-grid">
          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Explainability</p>
                <h2>Routing decision</h2>
              </div>
            </div>
            <div className="detail-list">
              <div>
                <span>Summary</span>
                <p>{routeResult.routing.explanation.summary}</p>
              </div>
              <div>
                <span>Selection</span>
                <p>{routeResult.routing.explanation.selection_reason}</p>
              </div>
              <div>
                <span>Compute tradeoff</span>
                <p>{routeResult.routing.explanation.compute_quality_tradeoff}</p>
              </div>
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Privacy</p>
                <h2>Data protection</h2>
              </div>
            </div>
            <div className="result-summary-grid compact">
              <div>
                <span>Risk</span>
                <strong>{privacy?.risk_level ?? 'none'}</strong>
              </div>
              <div>
                <span>Sensitive</span>
                <strong>
                  {privacy?.contains_sensitive_data ? 'Yes' : 'No'}
                </strong>
              </div>
              <div>
                <span>Local required</span>
                <strong>{privacy?.requires_local ? 'Yes' : 'No'}</strong>
              </div>
              <div>
                <span>Scope</span>
                <strong>{privacyPolicy?.execution_scope ?? 'local'}</strong>
              </div>
            </div>
            {privacy?.categories.length ? (
              <div className="chip-list">
                {privacy.categories.map((category) => (
                  <span key={category}>{category}</span>
                ))}
              </div>
            ) : null}
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Analytics</p>
                <h2>Route metrics</h2>
              </div>
            </div>
            <div className="result-summary-grid compact">
              <div>
                <span>Attempts</span>
                <strong>{analytics?.attempt_count ?? '—'}</strong>
              </div>
              <div>
                <span>Tokens</span>
                <strong>{analytics?.total_tokens ?? '—'}</strong>
              </div>
              <div>
                <span>Latency</span>
                <strong>
                  {analytics
                    ? `${formatNumber(analytics.total_latency_seconds)}s`
                    : '—'}
                </strong>
              </div>
              <div>
                <span>Compute</span>
                <strong>
                  {analytics
                    ? formatNumber(analytics.normalized_compute_cost)
                    : '—'}
                </strong>
              </div>
            </div>
          </article>
        </section>
      )}
    </>
  )
}
