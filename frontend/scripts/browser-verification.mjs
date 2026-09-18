import {
  chromium,
} from 'playwright-core'

import {
  existsSync,
} from 'node:fs'


const candidates = [
  process.env.AURA_BROWSER_PATH,
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
].filter(Boolean)


const executablePath =
  candidates.find(
    (candidate) =>
      existsSync(candidate),
  )


if (!executablePath) {
  throw new Error(
    'No supported installed Chrome/Edge executable found.',
  )
}


console.log(
  'BROWSER EXECUTABLE:',
  executablePath,
)


const browser =
  await chromium.launch({
    executablePath,
    headless: true,
  })


try {
  const page =
    await browser.newPage({
      viewport: {
        width: 1440,
        height: 1000,
      },
    })


  const consoleErrors = []

  page.on(
    'console',
    (message) => {
      if (
        message.type() === 'error'
      ) {
        consoleErrors.push(
          message.text(),
        )
      }
    },
  )


  console.log()
  console.log(
    '[A] Loading real Vite frontend...',
  )

  const response =
    await page.goto(
      'http://127.0.0.1:5173',
      {
        waitUntil: 'networkidle',
      },
    )


  if (
    !response
    || !response.ok()
  ) {
    throw new Error(
      'Frontend did not return a successful response.',
    )
  }


  await page
    .getByText(
      'System healthy',
    )
    .waitFor()


  console.log(
    'REAL BROWSER FRONTEND LOAD: PASS',
  )


  console.log()
  console.log(
    '[B] Verifying model registry rendering...',
  )


  await page
    .getByText(
      'qwen3:1.7b',
      {
        exact: true,
      },
    )
    .first()
    .waitFor()


  await page
    .getByText(
      'qwen3:4b',
      {
        exact: true,
      },
    )
    .first()
    .waitFor()


  await page
    .getByText(
      'qwen3:8b',
      {
        exact: true,
      },
    )
    .first()
    .waitFor()


  console.log(
    'REAL BROWSER MODEL REGISTRY: PASS',
  )


  console.log()
  console.log(
    '[C] Verifying working navigation...',
  )


  const multiTaskNav =
    page.getByRole(
      'button',
      {
        name: 'Multi-Task',
        exact: true,
      },
    )


  await multiTaskNav.click()


  if (
    await multiTaskNav.getAttribute(
      'aria-current',
    )
    !== 'page'
  ) {
    throw new Error(
      'Multi-Task navigation did not become active.',
    )
  }


  await page
    .locator(
      '#multi-task',
    )
    .waitFor()


  console.log(
    'REAL BROWSER NAVIGATION: PASS',
  )


  console.log()
  console.log(
    '[D] Executing real single-route request...',
  )


  await page
    .getByRole(
      'button',
      {
        name: 'Route Prompt',
        exact: true,
      },
    )
    .first()
    .click()


  const routePanel =
    page.locator(
      '#route-prompt',
    )


  const prompt =
    routePanel.locator(
      '#prompt',
    )


  await prompt.fill(
    'Extract the email alice@example.com from this sentence.',
  )


  await routePanel
    .getByRole(
      'button',
      {
        name: /Route Prompt/i,
      },
    )
    .click()


  await routePanel
    .getByText(
      'alice@example.com',
      {
        exact: true,
      },
    )
    .waitFor({
      timeout: 120000,
    })


  await routePanel
    .getByText(
      'qwen3:1.7b',
      {
        exact: true,
      },
    )
    .waitFor()


  await page
    .getByText(
      'local_only',
      {
        exact: true,
      },
    )
    .waitFor()


  console.log(
    'REAL BROWSER SINGLE ROUTE: PASS',
  )


  console.log()
  console.log(
    '[E] Verifying adaptive learning dashboard...',
  )


  const learningNav =
    page.getByRole(
      'button',
      {
        name: 'Learning',
        exact: true,
      },
    )


  await learningNav.click()


  const learningPanel =
    page.locator(
      '#learning',
    )


  await learningPanel
    .getByRole(
      'button',
      {
        name: /Load Learning Data/i,
      },
    )
    .click()


  await learningPanel
    .getByText(
      'Current recommendation',
      {
        exact: true,
      },
    )
    .waitFor()


  await learningPanel
    .getByText(
      'Historical performance',
      {
        exact: true,
      },
    )
    .waitFor()


  console.log(
    'REAL BROWSER LEARNING DASHBOARD: PASS',
  )


  console.log()
  console.log(
    '[F] Verifying mobile viewport...',
  )


  await page.setViewportSize({
    width: 390,
    height: 844,
  })


  await page.waitForTimeout(
    300,
  )


  const layout =
    await page.evaluate(() => ({
      innerWidth:
        window.innerWidth,

      scrollWidth:
        document.documentElement.scrollWidth,

      bodyWidth:
        document.body.scrollWidth,
    }))


  console.log(
    'MOBILE LAYOUT:',
    layout,
  )


  if (
    layout.scrollWidth
      > layout.innerWidth + 2
    ||
    layout.bodyWidth
      > layout.innerWidth + 2
  ) {
    throw new Error(
      'Mobile layout has unexpected horizontal overflow.',
    )
  }


  console.log(
    'REAL BROWSER MOBILE RESPONSIVE: PASS',
  )


  console.log()
  console.log(
    '[G] Checking browser console...',
  )


  if (
    consoleErrors.length > 0
  ) {
    console.log(
      'CONSOLE ERRORS:',
      consoleErrors,
    )

    throw new Error(
      'Browser console contains errors.',
    )
  }


  console.log(
    'REAL BROWSER CONSOLE: PASS',
  )


  console.log()
  console.log(
    'AURA REAL BROWSER E2E: PASS',
  )
}
finally {
  await browser.close()
}
