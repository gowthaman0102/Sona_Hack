import {
  type FormEvent,
  useState,
} from 'react'

import { multiRoutePrompt } from '../api/client'
import type { MultiTaskExecutionResult } from '../api/types'


function formatNumber(
  value: number | null | undefined,
  digits = 2,
) {
  if (value === null || value === undefined) {
    return '—'
  }

  return value.toFixed(digits)
}


export default function MultiTaskPage() {
  const [multiPrompt, setMultiPrompt] = useState(
    'Summarize why database indexes improve performance; extract the email alice@example.com; and explain when a full table scan may still be useful.',
  )
  const [multiResult, setMultiResult] =
    useState<MultiTaskExecutionResult | null>(null)
  const [multiRouting, setMultiRouting] = useState(false)
  const [multiError, setMultiError] =
    useState<string | null>(null)

  async function handleMultiRoute(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    const cleanPrompt = multiPrompt.trim()

    if (!cleanPrompt) {
      setMultiError('Enter a multi-task prompt before routing.')
      return
    }

    try {
      setMultiRouting(true)
      setMultiError(null)
      setMultiResult(null)

      const result = await multiRoutePrompt({
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

  return (
    <section className="panel multi-task-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Multi-Task Routing</p>
          <h2>Decompose and route multiple tasks</h2>
        </div>
        <span className="panel-tag">Live /multi-route</span>
      </div>

      <form className="multi-task-form" onSubmit={handleMultiRoute}>
        <label className="prompt-label" htmlFor="multi-prompt">
          Multi-task prompt
        </label>
        <textarea
          id="multi-prompt"
          onChange={(event) => setMultiPrompt(event.target.value)}
          placeholder="Enter multiple independent tasks..."
          rows={5}
          value={multiPrompt}
        />

        <div className="multi-task-actions">
          <div>
            <strong>Independent task routing</strong>
            <span>
              Each task receives its own model, confidence, privacy policy, and analytics.
            </span>
          </div>
          <button
            className="primary-button"
            disabled={multiRouting}
            type="submit"
          >
            {multiRouting ? 'Routing tasks...' : 'Route Multi-Task'}
            <span aria-hidden="true">?</span>
          </button>
        </div>
      </form>

      {multiError && (
        <div className="route-error" role="alert">
          {multiError}
        </div>
      )}

      {multiResult && (
        <div className="multi-task-results">
          <div className="multi-overview-grid">
            <div>
              <span>Multi-task</span>
              <strong>
                {multiResult.is_multi_task ? 'Detected' : 'Single task'}
              </strong>
            </div>
            <div>
              <span>Tasks</span>
              <strong>{multiResult.task_count}</strong>
            </div>
            <div>
              <span>Total attempts</span>
              <strong>{multiResult.analytics.total_attempt_count}</strong>
            </div>
            <div>
              <span>Total tokens</span>
              <strong>{multiResult.analytics.total_tokens}</strong>
            </div>
            <div>
              <span>Latency</span>
              <strong>
                {formatNumber(multiResult.analytics.total_latency_seconds)}s
              </strong>
            </div>
            <div>
              <span>Compute</span>
              <strong>
                {formatNumber(multiResult.analytics.normalized_compute_cost)}
              </strong>
            </div>
          </div>

          <section className="aggregated-response">
            <span>Aggregated Response</span>
            <p>{multiResult.aggregated_response}</p>
          </section>

          <div className="subtask-grid">
            {multiResult.tasks.map((task) => (
              <article className="subtask-card" key={task.index}>
                <div className="subtask-header">
                  <div>
                    <span>Task {task.index}</span>
                    <strong>{task.task_type}</strong>
                  </div>
                  <span className={`tier-pill ${task.selected_tier}`}>
                    {task.selected_tier.toUpperCase()}
                  </span>
                </div>

                <p className="subtask-text">{task.task}</p>
                <div className="subtask-response">{task.response}</div>

                <div className="subtask-metrics">
                  <div>
                    <span>Model</span>
                    <strong>{task.selected_model}</strong>
                  </div>
                  <div>
                    <span>Tokens</span>
                    <strong>{task.analytics.total_tokens}</strong>
                  </div>
                  <div>
                    <span>Latency</span>
                    <strong>
                      {formatNumber(task.analytics.total_latency_seconds)}s
                    </strong>
                  </div>
                </div>

                {task.escalation.attempts.length > 1 && (
                  <div className="attempt-path">
                    <span>Escalation path</span>
                    <div>
                      {task.escalation.attempts.map((attempt, attemptIndex) => (
                        <span
                          key={`${task.index}-${attemptIndex}-${attempt.tier}`}
                        >
                          {attempt.tier.toUpperCase()} ?{' '}
                          {Math.round(attempt.confidence_score * 100)}%
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
