import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react'

import userEvent from '@testing-library/user-event'

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
      display_name: 'Qwen3 1.7B',
      parameter_size: '1.7B',
      compute_score: 1,
      expected_speed: 'fast',
      description: 'Low tier',
      installed: true,
    },
    {
      tier: 'medium',
      model_name: 'qwen3:4b',
      display_name: 'Qwen3 4B',
      parameter_size: '4B',
      compute_score: 2,
      expected_speed: 'balanced',
      description: 'Medium tier',
      installed: true,
    },
    {
      tier: 'high',
      model_name: 'qwen3:8b',
      display_name: 'Qwen3 8B',
      parameter_size: '8B',
      compute_score: 4,
      expected_speed: 'slower',
      description: 'High tier',
      installed: true,
    },
  ],
}


function jsonResponse(
  payload: unknown,
) {
  return Promise.resolve(
    new Response(
      JSON.stringify(payload),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      },
    ),
  )
}


describe('AURA dashboard', () => {
  beforeEach(() => {
    vi.restoreAllMocks()

    vi
      .spyOn(
        Element.prototype,
        'scrollIntoView',
      )
      .mockImplementation(
        () => {},
      )
  })


  it('loads live system health and models', async () => {
    vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(
        (input) => {
          const url =
            input.toString()

          if (url.endsWith('/health')) {
            return jsonResponse(
              healthResponse,
            )
          }

          if (url.endsWith('/models')) {
            return jsonResponse(
              modelsResponse,
            )
          }

          throw new Error(
            `Unexpected URL: ${url}`,
          )
        },
      )

    render(
      <App />,
    )

    await waitFor(() => {
      expect(
        screen.getByText(
          'System healthy',
        ),
      ).toBeInTheDocument()
    })

    expect(
      screen.getByText(
        'qwen3:1.7b',
      ),
    ).toBeInTheDocument()

    expect(
      screen.getByText(
        'qwen3:4b',
      ),
    ).toBeInTheDocument()

    expect(
      screen.getByText(
        'qwen3:8b',
      ),
    ).toBeInTheDocument()
  })


  it('switches active navigation and scrolls to multi-task', async () => {
    const scrollSpy =
      vi.mocked(
        Element.prototype.scrollIntoView,
      )

    vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(
        (input) => {
          const url =
            input.toString()

          if (url.endsWith('/health')) {
            return jsonResponse(
              healthResponse,
            )
          }

          if (url.endsWith('/models')) {
            return jsonResponse(
              modelsResponse,
            )
          }

          throw new Error(
            `Unexpected URL: ${url}`,
          )
        },
      )

    render(
      <App />,
    )

    const multiTaskButton =
      screen.getByRole(
        'button',
        {
          name: 'Multi-Task',
        },
      )

    await userEvent.click(
      multiTaskButton,
    )

    expect(
      multiTaskButton,
    ).toHaveAttribute(
      'aria-current',
      'page',
    )

    expect(
      scrollSpy,
    ).toHaveBeenCalled()
  })


  it('renders a real-looking single-route result', async () => {
    vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(
        (input) => {
          const url =
            input.toString()

          if (url.endsWith('/health')) {
            return jsonResponse(
              healthResponse,
            )
          }

          if (url.endsWith('/models')) {
            return jsonResponse(
              modelsResponse,
            )
          }

          if (url.endsWith('/analysis')) {
            return jsonResponse({
              task_type: 'extraction',
              complexity_score: 1,
              reasoning_required: false,
              recommended_tier: 'low',
              explanation: 'extraction task baseline',
              features: {
                word_count: 8,
                has_code: false,
                has_reasoning_markers: false,
                has_multiple_requirements: false,
              },
            })
          }

          if (url.endsWith('/route')) {
            return jsonResponse({
              prompt:
                'Extract alice@example.com',
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
                    word_count: 8,
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
                  override_reason: null,
                  signals: [],
                },
              },
              response:
                'alice@example.com',
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
                attempts: [
                  {
                    tier: 'low',
                    model_name: 'qwen3:1.7b',
                    confidence_score: 1,
                    confidence_level: 'high',
                    should_escalate: false,
                    reasons: [],
                  },
                ],
              },
              privacy: {
                contains_sensitive_data: true,
                risk_level: 'medium',
                requires_local: true,
                categories: [
                  'email',
                ],
                signals: [
                  'email_detected',
                ],
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
                total_prompt_tokens: 40,
                total_output_tokens: 16,
                total_tokens: 56,
                total_latency_seconds: 2.698,
                normalized_compute_cost: 2.698,
                final_attempt_compute_cost: 2.698,
                escalation_overhead_compute: 0,
                attempts: [
                  {
                    tier: 'low',
                    model_name: 'qwen3:1.7b',
                    compute_score: 1,
                    confidence_score: 1,
                    confidence_level: 'high',
                    should_escalate: false,
                    prompt_tokens: 40,
                    output_tokens: 16,
                    total_tokens: 56,
                    latency_seconds: 2.698,
                    tokens_per_second: 5.93,
                    normalized_compute_cost: 2.698,
                  },
                ],
              },
            })
          }

          throw new Error(
            `Unexpected URL: ${url}`,
          )
        },
      )

    const { container } = render(
      <App />,
    )

    await screen.findByText(
      'System healthy',
    )

    const routePanel =
      container.querySelector(
        '#route-prompt',
      )

    expect(
      routePanel,
    ).not.toBeNull()

    const routeScope =
      within(
        routePanel as HTMLElement,
      )

    const prompt =
      routeScope.getByLabelText(
        'Prompt',
      )

    fireEvent.change(
      prompt,
      {
        target: {
          value:
            'Extract alice@example.com',
        },
      },
    )

    await userEvent.click(
      routeScope.getByRole(
        'button',
        {
          name: /Route Prompt/i,
        },
      ),
    )

    await waitFor(() => {
      expect(
        screen.getByText(
          'alice@example.com',
        ),
      ).toBeInTheDocument()
    })

    expect(
      routeScope.getByText(
        'qwen3:1.7b',
      ),
    ).toBeInTheDocument()

    expect(
      screen.getByText(
        'local_only',
      ),
    ).toBeInTheDocument()
  })


  it('renders multi-task results', async () => {
    vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(
        (input) => {
          const url =
            input.toString()

          if (url.endsWith('/health')) {
            return jsonResponse(
              healthResponse,
            )
          }

          if (url.endsWith('/models')) {
            return jsonResponse(
              modelsResponse,
            )
          }

          if (url.endsWith('/multi-route')) {
            return jsonResponse({
              original_prompt:
                'Extract and summarize',
              is_multi_task: true,
              task_count: 2,
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
                    reason: 'No escalation',
                    attempts: [
                      {
                        tier: 'low',
                        model_name: 'qwen3:1.7b',
                        confidence_score: 1,
                        confidence_level: 'high',
                        should_escalate: false,
                        reasons: [],
                      },
                    ],
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
                    reason: 'Local execution required',
                  },
                  analytics: {
                    attempt_count: 1,
                    total_prompt_tokens: 50,
                    total_output_tokens: 10,
                    total_tokens: 60,
                    total_latency_seconds: 1,
                    normalized_compute_cost: 1,
                    final_attempt_compute_cost: 1,
                    escalation_overhead_compute: 0,
                    attempts: [],
                  },
                },
                {
                  index: 2,
                  task: 'Summarize indexes',
                  task_type: 'summarization',
                  recommended_tier: 'medium',
                  selected_tier: 'medium',
                  selected_model: 'qwen3:4b',
                  compute_score: 2,
                  thinking_enabled: false,
                  response: 'Indexes reduce scan work.',
                  confidence: {
                    score: 1,
                    level: 'high',
                    should_escalate: false,
                    reasons: [],
                    response_word_count: 4,
                  },
                  escalation: {
                    escalated: false,
                    initial_tier: 'medium',
                    final_tier: 'medium',
                    reason: 'No escalation',
                    attempts: [
                      {
                        tier: 'medium',
                        model_name: 'qwen3:4b',
                        confidence_score: 1,
                        confidence_level: 'high',
                        should_escalate: false,
                        reasons: [],
                      },
                    ],
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
                    reason: 'Local execution required',
                  },
                  analytics: {
                    attempt_count: 1,
                    total_prompt_tokens: 80,
                    total_output_tokens: 20,
                    total_tokens: 100,
                    total_latency_seconds: 2,
                    normalized_compute_cost: 4,
                    final_attempt_compute_cost: 4,
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
                task_count: 2,
                total_attempt_count: 2,
                total_prompt_tokens: 130,
                total_output_tokens: 30,
                total_tokens: 160,
                total_latency_seconds: 3,
                normalized_compute_cost: 5,
                final_attempt_compute_cost: 5,
                escalation_overhead_compute: 0,
              },
              aggregated_response:
                'Task 1 - Extraction\nalice@example.com\n\nTask 2 - Summarization\nIndexes reduce scan work.',
              total_prompt_tokens: 130,
              total_output_tokens: 30,
              total_latency_seconds: 3,
              total_compute_score: 3,
            })
          }

          throw new Error(
            `Unexpected URL: ${url}`,
          )
        },
      )

    const { container } = render(
      <App />,
    )

    await screen.findByText(
      'System healthy',
    )

    const multiTaskPanel =
      container.querySelector(
        '#multi-task',
      )

    expect(
      multiTaskPanel,
    ).not.toBeNull()

    const multiTaskScope =
      within(
        multiTaskPanel as HTMLElement,
      )

    await userEvent.click(
      multiTaskScope.getByRole(
        'button',
        {
          name: /Route Multi-Task/i,
        },
      ),
    )

    await waitFor(() => {
      expect(
        screen.getByText(
          'Indexes reduce scan work.',
        ),
      ).toBeInTheDocument()
    })

    expect(
      screen.getByText(
        'Aggregated Response',
      ),
    ).toBeInTheDocument()

    expect(
      multiTaskScope.getByText(
        'qwen3:4b',
      ),
    ).toBeInTheDocument()
  })


  it('renders adaptive learning history and recommendation', async () => {
    vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(
        (input) => {
          const url =
            input.toString()

          if (url.endsWith('/health')) {
            return jsonResponse(
              healthResponse,
            )
          }

          if (url.endsWith('/models')) {
            return jsonResponse(
              modelsResponse,
            )
          }

          if (url.endsWith('/learning/history')) {
            return jsonResponse({
              'extraction::low': {
                task_type: 'extraction',
                tier: 'low',
                attempts: 3,
                successes: 3,
                failures: 0,
                average_confidence: 1,
                average_latency_seconds: 1.485,
                average_normalized_compute_cost: 1.485,
                reliability_score: 0.8,
              },
            })
          }

          if (
            url.includes(
              '/learning/recommendation/extraction',
            )
          ) {
            return jsonResponse({
              task_type: 'extraction',
              baseline_tier: 'low',
              recommended_tier: 'low',
              learning_applied: false,
              reason:
                'Insufficient historical evidence for the baseline tier.',
              candidates: [
                {
                  tier: 'low',
                  attempts: 3,
                  reliability_score: 0.8,
                },
                {
                  tier: 'medium',
                  attempts: 0,
                  reliability_score: 0.5,
                },
                {
                  tier: 'high',
                  attempts: 0,
                  reliability_score: 0.5,
                },
              ],
            })
          }

          throw new Error(
            `Unexpected URL: ${url}`,
          )
        },
      )

    const { container } = render(
      <App />,
    )

    await screen.findByText(
      'System healthy',
    )

    const learningPanel =
      container.querySelector(
        '#learning',
      )

    expect(
      learningPanel,
    ).not.toBeNull()

    const learningScope =
      within(
        learningPanel as HTMLElement,
      )

    await userEvent.click(
      learningScope.getByRole(
        'button',
        {
          name: /Load Learning Data/i,
        },
      ),
    )

    await waitFor(() => {
      expect(
        screen.getByText(
          'Insufficient historical evidence for the baseline tier.',
        ),
      ).toBeInTheDocument()
    })

    expect(
      learningScope.getAllByText(
        '80%',
      ).length,
    ).toBeGreaterThanOrEqual(1)

    expect(
      learningScope.getByText(
        '3 attempts',
      ),
    ).toBeInTheDocument()
  })
})
