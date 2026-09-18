import {
  useEffect,
  useMemo,
  useState,
} from 'react'
import {
  NavLink,
  Outlet,
} from 'react-router-dom'

import {
  API_BASE_URL,
  getHealth,
  getModels,
} from '../api/client'
import type {
  HealthResponse,
  ModelInfo,
} from '../api/types'
import AuraSessionProvider from '../context/AuraSessionProvider'


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


const navigation = [
  {
    label: 'Overview',
    path: '/',
  },
  {
    label: 'Route Prompt',
    path: '/route',
  },
  {
    label: 'Multi-Task',
    path: '/multi-task',
  },
]


export default function AppLayout() {
  const [health, setHealth] =
    useState<HealthResponse | null>(null)

  const [models, setModels] =
    useState<ModelInfo[]>(fallbackModels)

  const [loadingSystem, setLoadingSystem] =
    useState(true)

  const [systemError, setSystemError] =
    useState<string | null>(null)


  useEffect(() => {
    let cancelled = false

    async function loadSystemData() {
      try {
        setLoadingSystem(true)
        setSystemError(null)

        const [healthResult, modelResult] =
          await Promise.all([
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

  const context = useMemo(
    () => ({
      health,
      models,
      loadingSystem,
      systemError,
      backendHealthy,
    }),
    [
      backendHealthy,
      health,
      loadingSystem,
      models,
      systemError,
    ],
  )


  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            A
          </div>

          <div>
            <strong>AURA</strong>
            <span>LLM Router</span>
          </div>
        </div>

        <nav
          className="nav-list"
          aria-label="Primary navigation"
        >
          {navigation.map((item) => (
            <NavLink
              className={({ isActive }) =>
                isActive
                  ? 'nav-item active'
                  : 'nav-item'}
              end={item.path === '/'}
              key={item.path}
              to={item.path}
            >
              {() => (
                <>
                  <span className="nav-dot" />
                    {item.label}
                </>
              )}
            </NavLink>
          ))}
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
            <strong>Local AI Stack</strong>
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
            <h1>Intelligent LLM Routing</h1>
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
          <div className="system-alert" role="alert">
            <strong>Backend connection unavailable.</strong>
            <span>{systemError}</span>
          </div>
        )}

        <AuraSessionProvider>
          <Outlet context={context} />
        </AuraSessionProvider>
      </main>
    </div>
  )
}
