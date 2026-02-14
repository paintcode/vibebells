/**
 * Playwright Configuration for Electron E2E Tests
 * @see https://playwright.dev/docs/test-configuration
 */

const { defineConfig } = require('@playwright/test');
const path = require('path');

module.exports = defineConfig({
  testDir: './e2e',
  
  // Maximum time one test can run
  timeout: 60 * 1000,
  
  // Test execution settings
  fullyParallel: false, // Run tests sequentially for Electron
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Only 1 worker for Electron tests
  
  // Reporter configuration
  reporter: [
    ['list'],
    ['html', { outputFolder: 'e2e-report', open: 'never' }],
    ['json', { outputFile: 'e2e-results.json' }]
  ],
  
  // Shared settings for all tests
  use: {
    // Base URL for API tests (backend)
    baseURL: 'http://localhost:5000',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Trace on failure
    trace: 'on-first-retry',
  },
  
  // Test match patterns
  testMatch: '**/*.spec.js',
  
  // Global setup/teardown
  globalSetup: path.join(__dirname, 'e2e', 'helpers', 'global-setup.js'),
  globalTeardown: path.join(__dirname, 'e2e', 'helpers', 'global-teardown.js'),
});
