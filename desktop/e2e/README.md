# E2E Tests for Vibebells Desktop

Automated end-to-end tests for the Vibebells desktop application using Playwright.

## Overview

These tests verify the complete user workflow:
1. **App Launch**: Electron app starts successfully
2. **Backend Health**: Python backend spawns and responds
3. **Frontend Loading**: React UI renders correctly
4. **MIDI Upload**: File selection and upload works
5. **Player Configuration**: Adding and configuring players
6. **Arrangement Generation**: Creating bell arrangements
7. **CSV Export**: Exporting arrangements to CSV

## Test Structure

```
e2e/
├── app.spec.js           # Main UI/workflow tests
├── api.spec.js           # Backend API integration tests
├── fixtures/             # Test data (MIDI files)
│   └── test-song.mid
├── helpers/              # Utility functions
│   ├── electron-helpers.js
│   ├── global-setup.js
│   └── global-teardown.js
└── screenshots/          # Test screenshots (auto-generated)
```

## Running Tests

### Prerequisites

```bash
# Install dependencies (already done during setup)
npm install
```

### Run All Tests

```bash
# Headless mode (CI/automation)
npm run test:e2e

# Headed mode (see the app while testing)
npm run test:e2e:headed

# Debug mode (step through tests)
npm run test:e2e:debug

# UI mode (interactive test runner)
npm run test:e2e:ui
```

### Run Specific Tests

```bash
# Run only UI tests
npx playwright test app.spec.js

# Run only API tests
npx playwright test api.spec.js

# Run tests matching pattern
npx playwright test --grep "CSV"
```

### View Test Results

```bash
# Open HTML report
npm run test:e2e:report

# View in terminal during test run
npm run test:e2e -- --reporter=list
```

## Test Configuration

Configuration is in `playwright.config.js`:

- **Timeout**: 60 seconds per test
- **Workers**: 1 (sequential execution for Electron)
- **Retries**: 0 in dev, 2 in CI
- **Screenshots**: On failure only
- **Videos**: Retained on failure
- **Reports**: HTML, JSON, list

## Writing New Tests

### Basic Test Template

```javascript
const { test, expect } = require('@playwright/test');
const { launchElectronApp } = require('./helpers/electron-helpers');

test.describe('My Feature', () => {
  let electronApp, window;
  
  test.beforeAll(async () => {
    const result = await launchElectronApp();
    electronApp = result.app;
    window = result.window;
  });
  
  test.afterAll(async () => {
    await electronApp.close();
  });
  
  test('should do something', async () => {
    // Your test code here
    await expect(window.locator('h1')).toBeVisible();
  });
});
```

### Helper Functions

Use the helpers in `helpers/electron-helpers.js`:

```javascript
const {
  launchElectronApp,      // Launch app for testing
  waitForBackend,         // Wait for backend to be ready
  waitForFrontend,        // Wait for frontend to load
  uploadMidiFile,         // Upload a MIDI file
  generateArrangements,   // Generate arrangements
  takeScreenshot          // Save screenshot for debugging
} = require('./helpers/electron-helpers');
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend && pip install -r requirements.txt
          cd ../frontend && npm install
          cd ../desktop && npm install
      
      - name: Build desktop app
        run: npm run build:win
        working-directory: desktop
      
      - name: Run E2E tests
        run: npm run test:e2e
        working-directory: desktop
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-report
          path: desktop/e2e-report/
```

## Troubleshooting

### Tests Fail to Launch App

- Ensure the app builds successfully: `npm run pack`
- Check that Electron is installed: `npm list electron`
- Verify Python backend dependencies are installed

### Backend Not Responding

- Check backend logs in test output
- Increase timeout in `waitForBackend()` helper
- Verify backend port 5000 is not already in use

### MIDI Upload Fails

- Ensure `e2e/fixtures/test-song.mid` exists
- Check file permissions
- Verify MIDI file is not corrupted

### Screenshots Not Saving

- Check `e2e/screenshots/` directory permissions
- Ensure directory is created (global-setup should handle this)
- Use `takeScreenshot()` helper for manual screenshots

### Flaky Tests

- Add explicit waits: `await window.waitForTimeout(1000)`
- Use `waitForSelector` instead of fixed timeouts
- Increase test timeout in playwright.config.js

## Test Coverage

Current test coverage:

- ✅ App launch and window creation
- ✅ Backend health check
- ✅ Frontend rendering
- ✅ File upload UI
- ✅ Player configuration UI
- ✅ Arrangement generation UI
- ✅ CSV export UI
- ✅ Backend API endpoints
- ✅ Error handling
- ⏳ Native file dialogs (requires additional mocking)
- ⏳ Application menu actions
- ⏳ Window operations (resize, minimize, close)

## Future Enhancements

- [ ] Add visual regression testing
- [ ] Test all 3 arrangement strategies
- [ ] Test edge cases (1 player, 20 players)
- [ ] Test with multiple MIDI files
- [ ] Mock native file dialogs for full automation
- [ ] Add performance benchmarking
- [ ] Cross-platform testing (macOS, Linux)

## Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Electron Testing with Playwright](https://playwright.dev/docs/api/class-electron)
- [Vibebells Project Documentation](../README.md)

## Support

For issues or questions about E2E tests:
1. Check this README
2. Review test output and screenshots
3. Check Playwright documentation
4. Open an issue with test logs and screenshots
