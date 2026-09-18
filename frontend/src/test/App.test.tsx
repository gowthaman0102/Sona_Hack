import {
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  MemoryRouter,
  useLocation,
} from 'react-router-dom'
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import App from '../App'


const healthResponse = {
  status: 'healthy',
  service: 'aura-backend',
}


const modelsResponse = {
  count: 3,
  models: [
    {
      tier: 'low',
      model_name: 'qwen3:1.7b',
      compute_score: 1,
      description: 'Low tier',
    },
    {
      tier: 'medium',
      model_name: 'qwen3:4b',
      compute_score: 2,
      description: 'Medium tier',
    },
    {
      tier: 'high',
      model_name: 'qwen3:8b',
      compute_score: 4,
      description: 'High tier',
    },
  ],
}


function jsonResponse(payload: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify(payload), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    }),
  )
}


function deferredResponse() {
  let resolvePromise: (response: Response) => void = () => {}
  const promise = new Promise<Response>((resolve) => {
    resolvePromise = resolve
  })

  return {
    promise,
    resolve: resolvePromise,
  }
}


function routeResponse() {
  return {
    prompt: 'Extract alice@example.com',
    routing: {
      recommended_tier: 'low',
      selected_tier: 'low',
      selected_model: 'qwen3:1.7b',
      compute_score: 1,
      override_applied: false,
      thinking_override_applied: false,
      thinking_enabled: false,
      analysis: {
        task_type: 'extraction',
        complexity_score: 1,
        reasoning_required: false,
        recommended_tier: 'low',
        explanation: 'extraction task baseline',
        features: {
          word_count: 2,
          has_code: false,
          has_reasoning_markers: false,
          has_multiple_requirements: false,
        },
      },
      explanation: {
        summary: 'LOW selected',
        selection_reason: 'Simple extraction',
        complexity_reason: 'Low complexity',
        reasoning_reason: 'No deep reasoning needed',
        compute_quality_tradeoff: 'Lowest compute tier',
        override_reason: '',
        signals: [],
      },
    },
    response: 'alice@example.com',
    confidence: {
      score: 1,
      level: 'high',
      should_escalate: false,
      reasons: [],
      response_word_count: 1,
    },
    escalation: {
      escalated: false,
      initial_tier: 'low',
      final_tier: 'low',
      reason: 'No escalation required.',
      attempts: [],
    },
    privacy: {
      contains_sensitive_data: true,
      risk_level: 'medium',
      requires_local: true,
      categories: ['email'],
      signals: ['email_detected'],
    },
    privacy_policy: {
      privacy_enforced: true,
      execution_scope: 'local_only',
      external_routing_allowed: false,
      selected_model_is_local: true,
      reason: 'Sensitive data requires local execution.',
    },
    analytics: {
      attempt_count: 1,
      total_prompt_tokens: 10,
      total_output_tokens: 1,
      total_tokens: 11,
      total_latency_seconds: 0.2,
      normalized_compute_cost: 0.2,
      final_attempt_compute_cost: 0.2,
      escalation_overhead_compute: 0,
      attempts: [],
    },
  }
}


function multiResponse() {
  return {
    original_prompt: 'Extract email',
    is_multi_task: true,
    task_count: 1,
    tasks: [
      {
        index: 1,
        task: 'Extract email',
        task_type: 'extraction',
        recommended_tier: 'low',
        selected_tier: 'low',
        selected_model: 'qwen3:1.7b',
        compute_score: 1,
        thinking_enabled: false,
        response: 'alice@example.com',
        confidence: {
          score: 1,
          level: 'high',
          should_escalate: false,
          reasons: [],
          response_word_count: 1,
        },
        escalation: {
          escalated: false,
          initial_tier: 'low',
          final_tier: 'low',
          reason: 'No escalation required.',
          attempts: [],
        },
        privacy: {
          contains_sensitive_data: true,
          risk_level: 'medium',
          requires_local: true,
          categories: ['email'],
          signals: ['email_detected'],
        },
        privacy_policy: {
          privacy_enforced: true,
          execution_scope: 'local_only',
          external_routing_allowed: false,
          selected_model_is_local: true,
          reason: 'Sensitive data requires local execution.',
        },
        analytics: {
          attempt_count: 1,
          total_prompt_tokens: 10,
          total_output_tokens: 1,
          total_tokens: 11,
          total_latency_seconds: 0.2,
          normalized_compute_cost: 0.2,
          final_attempt_compute_cost: 0.2,
          escalation_overhead_compute: 0,
          attempts: [],
        },
      },
    ],
    privacy: {
      contains_sensitive_data: true,
      risk_level: 'medium',
      requires_local: true,
      categories: ['email'],
      signals: ['email_detected'],
    },
    analytics: {
      task_count: 1,
      total_attempt_count: 1,
      total_prompt_tokens: 10,
      total_output_tokens: 1,
      total_tokens: 11,
      total_latency_seconds: 0.2,
      normalized_compute_cost: 0.2,
      final_attempt_compute_cost: 0.2,
      escalation_overhead_compute: 0,
    },
    aggregated_response: 'Task 1 - Extraction\nalice@example.com',
    total_prompt_tokens: 10,
    total_output_tokens: 1,
    total_latency_seconds: 0.2,
    total_compute_score: 1,
  }
}


function LocationProbe() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}


function renderApp(initialEntry = '/') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <LocationProbe />
      <App />
    </MemoryRouter>,
  )
}


function mockSystemFetch() {
  return vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
    const url = input.toString()

    if (url.endsWith('/health')) {
      return jsonResponse(healthResponse)
    }

    if (url.endsWith('/models')) {
      return jsonResponse(modelsResponse)
    }

    throw new Error(`Unexpected URL: ${url}`)
  })
}


describe('AURA routed dashboard', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders Overview at the root route', async () => {
    mockSystemFetch()
    renderApp('/')

    await screen.findByText('System healthy')

    expect(screen.getByText('Architecture status')).toBeInTheDocument()
    expect(screen.getByTestId('location')).toHaveTextContent('/')
  })

  it('renders Route Prompt at /route', async () => {
    mockSystemFetch()
    renderApp('/route')

    await screen.findByText('System healthy')

    expect(screen.getByRole('heading', { name: 'Route a prompt' }))
      .toBeInTheDocument()
    expect(screen.getByTestId('location')).toHaveTextContent('/route')
  })

  it('renders Multi-Task at /multi-task', async () => {
    mockSystemFetch()
    renderApp('/multi-task')

    await screen.findByText('System healthy')

    expect(
      screen.getByRole('heading', {
        name: 'Decompose and route multiple tasks',
      }),
    ).toBeInTheDocument()
    expect(screen.getByTestId('location')).toHaveTextContent('/multi-task')
  })

  it('navigates with sidebar links and updates the active link', async () => {
    mockSystemFetch()
    renderApp('/')

    await screen.findByText('System healthy')
    const navigation = screen.getByRole('navigation', {
      name: 'Primary navigation',
    })

    await userEvent.click(
      within(navigation).getByRole('link', {
        name: 'Route Prompt',
      }),
    )

    expect(screen.getByTestId('location')).toHaveTextContent('/route')
    expect(
      within(navigation).getByRole('link', {
        name: 'Route Prompt',
      }),
    ).toHaveAttribute('aria-current', 'page')

    await userEvent.click(
      within(navigation).getByRole('link', {
        name: 'Multi-Task',
      }),
    )
    expect(screen.getByTestId('location')).toHaveTextContent('/multi-task')

    await userEvent.click(
      within(navigation).getByRole('link', {
        name: 'Overview',
      }),
    )
    expect(screen.getByTestId('location')).toHaveTextContent('/')
  })

  it('redirects unknown routes to Overview', async () => {
    mockSystemFetch()
    renderApp('/not-a-real-page')

    await screen.findByText('Architecture status')

    expect(screen.getByTestId('location')).toHaveTextContent('/')
  })

  it('submits Route Prompt through analysis and route APIs', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = input.toString()

      if (url.endsWith('/health')) {
        return jsonResponse(healthResponse)
      }
      if (url.endsWith('/models')) {
        return jsonResponse(modelsResponse)
      }
      if (url.endsWith('/analysis')) {
        return jsonResponse(routeResponse().routing.analysis)
      }
      if (url.endsWith('/route')) {
        return jsonResponse(routeResponse())
      }

      throw new Error(`Unexpected URL: ${url}`)
    })

    renderApp('/route')
    await screen.findByText('System healthy')

    const routePage = screen.getByRole('heading', {
      name: 'Route a prompt',
    }).closest('article') as HTMLElement
    await userEvent.clear(within(routePage).getByLabelText('Prompt'))
    await userEvent.type(
      within(routePage).getByLabelText('Prompt'),
      'Extract alice@example.com',
    )
    await userEvent.click(
      within(routePage).getByRole('button', {
        name: /Route Prompt/i,
      }),
    )

    await screen.findByText('alice@example.com')
    expect(
      fetchMock.mock.calls.filter(([input]) =>
        input.toString().endsWith('/analysis'),
      ),
    ).toHaveLength(1)
    expect(
      fetchMock.mock.calls.filter(([input]) =>
        input.toString().endsWith('/route'),
      ),
    ).toHaveLength(1)

    await userEvent.click(
      within(routePage).getByRole('button', {
        name: /Route Prompt/i,
      }),
    )
    await screen.findByText('alice@example.com')
    expect(
      fetchMock.mock.calls.filter(([input]) =>
        input.toString().endsWith('/route'),
      ),
    ).toHaveLength(2)
  })

  it('shows stage-aware loading and clears it after success', async () => {
    const analysisPending = deferredResponse()
    const routePending = deferredResponse()

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = input.toString()

      if (url.endsWith('/health')) {
        return jsonResponse(healthResponse)
      }
      if (url.endsWith('/models')) {
        return jsonResponse(modelsResponse)
      }
      if (url.endsWith('/analysis')) {
        return analysisPending.promise
      }
      if (url.endsWith('/route')) {
        return routePending.promise
      }

      throw new Error(`Unexpected URL: ${url}`)
    })

    renderApp('/route')
    await screen.findByText('System healthy')

    const routePage = screen.getByRole('heading', {
      name: 'Route a prompt',
    }).closest('article') as HTMLElement
    const submitButton = within(routePage).getByRole('button', {
      name: /Route Prompt/i,
    })

    await userEvent.click(submitButton)

    expect(submitButton).toBeDisabled()
    expect(screen.getByRole('status')).toHaveTextContent(
      'Analyzing prompt...',
    )

    analysisPending.resolve(
      await jsonResponse(routeResponse().routing.analysis),
    )

    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent(
        'Generating response...',
      )
    })

    routePending.resolve(await jsonResponse(routeResponse()))

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    })
    expect(fetchMock.mock.calls.some(([input]) =>
      input.toString().endsWith('/route'),
    )).toBe(true)
  })

  it('clears loading feedback when routing fails', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = input.toString()

      if (url.endsWith('/health')) {
        return jsonResponse(healthResponse)
      }
      if (url.endsWith('/models')) {
        return jsonResponse(modelsResponse)
      }
      if (url.endsWith('/analysis')) {
        return jsonResponse(routeResponse().routing.analysis)
      }
      if (url.endsWith('/route')) {
        return Promise.reject(new Error('Route request failed'))
      }

      throw new Error(`Unexpected URL: ${url}`)
    })

    renderApp('/route')
    await screen.findByText('System healthy')
    await userEvent.click(
      screen.getByRole('button', {
        name: /Route Prompt/i,
      }),
    )

    await screen.findByRole('alert')
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([input]) =>
      input.toString().endsWith('/route'),
    )).toBe(true)
  })

  it('submits Multi-Task through the multi-route API', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = input.toString()

      if (url.endsWith('/health')) {
        return jsonResponse(healthResponse)
      }
      if (url.endsWith('/models')) {
        return jsonResponse(modelsResponse)
      }
      if (url.endsWith('/multi-route')) {
        return jsonResponse(multiResponse())
      }

      throw new Error(`Unexpected URL: ${url}`)
    })

    renderApp('/multi-task')
    await screen.findByText('System healthy')
    await userEvent.click(
      screen.getByRole('button', {
        name: /Route Multi-Task/i,
      }),
    )

    await screen.findByText('alice@example.com')
    expect(fetchMock.mock.calls.some(([input]) => input.toString().endsWith('/multi-route'))).toBe(true)
    expect(screen.getByText('Task 1')).toBeInTheDocument()
  })
})
