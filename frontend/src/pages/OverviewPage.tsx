import { useMemo } from 'react'

import { useAppLayout } from '../components/appLayoutContext'


export default function OverviewPage() {
  const {
    backendHealthy,
    health,
    loadingSystem,
    models,
  } = useAppLayout()

  const normalizedModels = useMemo(
    () =>
      [...models].sort(
        (left, right) =>
          left.compute_score - right.compute_score,
      ),
    [models],
  )

  return (
    <>
      <section
        className="metric-grid"
        aria-label="System overview"
      >
        <article className="metric-card">
          <span className="metric-label">Routing Engine</span>
          <strong>Adaptive</strong>
          <small>History-aware model selection</small>
        </article>

        <article className="metric-card">
          <span className="metric-label">Model Tiers</span>
          <strong>
            {loadingSystem
              ? '...'
              : `${models.length} Local`}
          </strong>
          <small>Loaded from /models</small>
        </article>

        <article className="metric-card">
          <span className="metric-label">Backend</span>
          <strong>
            {loadingSystem
              ? 'Checking'
              : backendHealthy
                ? 'Healthy'
                : 'Offline'}
          </strong>
          <small>{health?.service ?? 'aura-backend'}</small>
        </article>

        <article className="metric-card">
          <span className="metric-label">Last Route</span>
          <strong>—</strong>
          <small>Open Route Prompt to begin</small>
        </article>
      </section>

      <section className="content-grid">
        <article className="panel model-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Local Models</p>
              <h2>Model tiers</h2>
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
            {normalizedModels.map((item) => (
              <div
                className="tier-row"
                key={`${item.tier}-${item.model_name}`}
              >
                <div className={`tier-icon ${item.tier}`}>
                  {item.tier.slice(0, 1).toUpperCase()}
                </div>
                <div className="tier-copy">
                  <strong>{item.tier.toUpperCase()}</strong>
                  <span>{item.model_name}</span>
                  <small>
                    {item.description ?? 'Local Ollama model'}
                  </small>
                </div>
                <div className="compute-badge">
                  {item.compute_score}x
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">System</p>
              <h2>Architecture status</h2>
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
                <strong>Backend API</strong>
                <small>
                  {backendHealthy ? 'Connected' : 'Unavailable'}
                </small>
              </p>
            </div>
            <div>
              <span className="status-dot online" />
              <p>
                <strong>Privacy Engine</strong>
                <small>Enforced</small>
              </p>
            </div>
            <div>
              <span className="status-dot online" />
              <p>
                <strong>Learning Store</strong>
                <small>Persistent</small>
              </p>
            </div>
            <div>
              <span className="status-dot online" />
              <p>
                <strong>Analytics</strong>
                <small>Enabled</small>
              </p>
            </div>
          </div>
        </article>
      </section>

      <section className="bottom-grid">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Decision Pipeline</p>
              <h2>Why AURA routes intelligently</h2>
            </div>
          </div>

          <div className="feature-grid">
            <div className="feature">
              <span>01</span>
              <strong>Query Analysis</strong>
              <p>Classifies task type, complexity, and reasoning needs.</p>
            </div>
            <div className="feature">
              <span>02</span>
              <strong>Privacy Policy</strong>
              <p>Ensures sensitive workloads stay on local models.</p>
            </div>
            <div className="feature">
              <span>03</span>
              <strong>Confidence</strong>
              <p>Escalates when lower tiers do not meet quality needs.</p>
            </div>
            <div className="feature">
              <span>04</span>
              <strong>Adaptive Learning</strong>
              <p>Uses reliability history to improve future routing.</p>
            </div>
          </div>
        </article>
      </section>
    </>
  )
}
