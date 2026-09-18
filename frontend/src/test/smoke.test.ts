import {
  describe,
  expect,
  it,
} from 'vitest'


describe('AURA frontend test environment', () => {
  it('provides a browser-like DOM', () => {
    const element =
      document.createElement('div')

    element.textContent =
      'AURA test environment ready'

    document.body.appendChild(
      element,
    )

    expect(
      document.body,
    ).toHaveTextContent(
      'AURA test environment ready',
    )
  })
})
