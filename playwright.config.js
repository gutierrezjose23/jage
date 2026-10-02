import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 30000,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:5010',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    ...(process.env.PLAYWRIGHT_CHROME_PATH
      ? {
          launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH },
        }
      : {}),
  },
  webServer: {
    command: `"${process.env.JAGE_TEST_PYTHON || '.venv/Scripts/python.exe'}" tests/serve_e2e.py`,
    url: 'http://127.0.0.1:5010/api/session',
    reuseExistingServer: false,
    timeout: 30000,
  },
})
