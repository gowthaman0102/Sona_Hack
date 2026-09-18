import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import {
  analyzePrompt,
  getHealth,
  getLearningHistory,
  getLearningRecommendation,
  getModels,
  multiRoutePrompt,
  routePrompt,
} from '../api/client'


describe('AURA API client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })


  it('calls the health endpoint', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            status: 'healthy',
            service: 'aura-backend',
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        ),
      )

    const result =
      await getHealth()

    expect(
      fetchMock,
    ).toHaveBeenCalledTimes(1)

    expect(
      fetchMock.mock.calls[0][0]
        .toString()
        .endsWith('/health'),
    ).toBe(true)

    expect(
      result.status,
    ).toBe('healthy')
  })


  it('posts prompt analysis to /analysis', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            task_type: 'extraction',
            complexity_score: 1,
            reasoning_required: false,
            recommended_tier: 'low',
            explanation: 'extraction task baseline',
            features: {
              word_count: 3,
              has_code: false,
              has_reasoning_markers: false,
              has_multiple_requirements: false,
            },
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        ),
      )

    await analyzePrompt({
      prompt: 'extract this email',
    })

    expect(
      fetchMock,
    ).toHaveBeenCalledTimes(1)

    const [
      url,
      options,
    ] = fetchMock.mock.calls[0]

    expect(
      url.toString().endsWith('/analysis'),
    ).toBe(true)

    expect(
      options?.method,
    ).toBe('POST')

    expect(
      options?.body,
    ).toBe(
      JSON.stringify({
        prompt: 'extract this email',
      }),
    )
  })


  it('posts routing request to /route', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            prompt: 'hello',
            routing: {
              recommended_tier: 'low',
              selected_tier: 'low',
              selected_model: 'qwen3:1.7b',
              compute_score: 1,
              override_applied: false,
              thinking_override_applied: false,
              thinking_enabled: false,
              analysis: {
                task_type: 'general',
                complexity_score: 2,
                reasoning_required: false,
                recommended_tier: 'low',
                explanation: 'general task baseline',
                features: {
                  word_count: 1,
                  has_code: false,
                  has_reasoning_markers: false,
                  has_multiple_requirements: false,
                },
              },
              explanation: {
                summary: 'LOW selected',
                selection_reason: 'simple task',
                complexity_reason: 'low complexity',
                reasoning_reason: 'no reasoning required',
                compute_quality_tradeoff: 'lowest compute',
                override_reason: null,
                signals: [],
              },
            },
            response: 'Hello',
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        ),
      )

    await routePrompt({
      prompt: 'hello',
    })

    expect(
      fetchMock.mock.calls[0][0]
        .toString()
        .endsWith('/route'),
    ).toBe(true)

    expect(
      fetchMock.mock.calls[0][1]
        ?.method,
    ).toBe('POST')
  })


  it('posts multi-task requests to /multi-route', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            original_prompt: 'task one; task two',
            is_multi_task: true,
            task_count: 0,
            tasks: [],
            privacy: {
              contains_sensitive_data: false,
              risk_level: 'none',
              requires_local: false,
              categories: [],
              signals: [],
            },
            analytics: {
              task_count: 0,
              total_attempt_count: 0,
              total_prompt_tokens: 0,
              total_output_tokens: 0,
              total_tokens: 0,
              total_latency_seconds: 0,
              normalized_compute_cost: 0,
              final_attempt_compute_cost: 0,
              escalation_overhead_compute: 0,
            },
            aggregated_response: '',
            total_prompt_tokens: 0,
            total_output_tokens: 0,
            total_latency_seconds: 0,
            total_compute_score: 0,
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        ),
      )

    await multiRoutePrompt({
      prompt: 'task one; task two',
    })

    expect(
      fetchMock.mock.calls[0][0]
        .toString()
        .endsWith('/multi-route'),
    ).toBe(true)

    expect(
      fetchMock.mock.calls[0][1]
        ?.method,
    ).toBe('POST')
  })


  it('calls learning endpoints with expected paths', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(
          JSON.stringify({}),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        ),
      )

    await getLearningHistory()

    expect(
      fetchMock.mock.calls[0][0]
        .toString()
        .endsWith('/learning/history'),
    ).toBe(true)


    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          task_type: 'extraction',
          baseline_tier: 'low',
          recommended_tier: 'low',
          learning_applied: false,
          reason: 'No change',
          candidates: [],
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
          },
        },
      ),
    )

    await getLearningRecommendation(
      'extraction',
      'low',
    )

    const recommendationUrl =
      fetchMock.mock.calls[1][0]
        .toString()

    expect(
      recommendationUrl,
    ).toContain(
      '/learning/recommendation/extraction',
    )

    expect(
      recommendationUrl,
    ).toContain(
      'baseline_tier=low',
    )
  })


  it('calls /models', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            count: 0,
            models: [],
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        ),
      )

    await getModels()

    expect(
      fetchMock.mock.calls[0][0]
        .toString()
        .endsWith('/models'),
    ).toBe(true)
  })
})
