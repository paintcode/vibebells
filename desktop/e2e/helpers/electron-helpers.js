/**
 * Helper utilities for Electron E2E tests
 */

const { _electron: electron } = require('playwright');
const path = require('path');

/**
 * Launch Electron app for testing
 * @param {Object} options - Launch options
 * @param {boolean} options.useBuild - Use built executable instead of dev mode (default: true)
 * @returns {Promise<{app: ElectronApplication, window: Page}>}
 */
async function launchElectronApp(options = {}) {
  const { useBuild = true } = options;
  
  let executablePath;
  let args = [];
  
  if (useBuild) {
    // Use built executable for production-like testing
    const builtExePath = path.join(__dirname, '..', '..', 'dist', 'win-unpacked', 'Vibebells.exe');
    const fs = require('fs');
    if (!fs.existsSync(builtExePath)) {
      throw new Error(`Built executable not found at ${builtExePath}. Run 'npm run build:desktop' first.`);
    }
    executablePath = builtExePath;
  } else {
    // Use dev mode (requires electron installed)
    const electronPath = require('electron');
    const appPath = path.join(__dirname, '..', '..');
    executablePath = electronPath;
    args = [appPath];
  }
  
  // Launch Electron app
  const app = await electron.launch({
    executablePath,
    args,
    env: {
      ...process.env,
      NODE_ENV: 'test',
      E2E_TEST: 'true'
    }
  });
  
  // Wait for window to be ready
  const window = await app.firstWindow();
  await window.waitForLoadState('domcontentloaded');
  
  return { app, window };
}

/**
 * Wait for backend to be ready
 * @param {number} timeout - Maximum wait time in ms
 * @returns {Promise<boolean>}
 */
async function waitForBackend(timeout = 30000) {
  const startTime = Date.now();
  const url = 'http://localhost:5000/api/health';
  
  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'healthy') {
          return true;
        }
      }
    } catch (error) {
      // Backend not ready yet, continue waiting
    }
    
    // Wait 500ms before next attempt
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  throw new Error(`Backend not ready after ${timeout}ms`);
}

/**
 * Wait for frontend to be ready
 * @param {Page} window - Playwright page object
 * @param {number} timeout - Maximum wait time in ms
 * @returns {Promise<void>}
 */
async function waitForFrontend(window, timeout = 30000) {
  await window.waitForSelector('body', { timeout });
  
  // Wait for app content to render - look for the main heading
  await window.waitForFunction(() => {
    // Check for Next.js root or look for main content
    const nextRoot = document.querySelector('#__next');
    const mainHeading = document.querySelector('h1');
    const hasContent = document.body.textContent.includes('Handbell Arrangement Generator');
    return (nextRoot && nextRoot.children.length > 0) || mainHeading || hasContent;
  }, { timeout });
}

/**
 * Upload MIDI file via Electron API
 * @param {ElectronApplication} app - Electron app instance
 * @param {Page} window - Playwright page object
 * @param {string} filePath - Path to MIDI file
 * @returns {Promise<void>}
 */
async function uploadMidiFile(app, window, filePath) {
  // Get absolute path
  const absolutePath = path.resolve(filePath);
  
  // Evaluate in Electron context to trigger file selection
  await window.evaluate(async (filepath) => {
    // Simulate file selection by directly calling the upload handler
    // This bypasses the native file dialog for testing
    const file = new File(['dummy'], path.basename(filepath), { type: 'audio/midi' });
    
    // Find file input element
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
      // Create a synthetic file list
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      fileInput.files = dataTransfer.files;
      
      // Trigger change event
      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    }
  }, absolutePath);
}

/**
 * Generate arrangements via UI
 * @param {Page} window - Playwright page object
 * @returns {Promise<void>}
 */
async function generateArrangements(window) {
  // Click "Generate Arrangements" button
  const button = await window.locator('button:has-text("Generate Arrangements")');
  await button.waitFor({ state: 'visible' });
  await button.click();
  
  // Wait for arrangements to load
  await window.waitForSelector('[data-testid="arrangement-results"]', {
    timeout: 30000,
    state: 'visible'
  });
}

/**
 * Clean up test artifacts
 * @returns {Promise<void>}
 */
async function cleanupTestArtifacts() {
  const fs = require('fs').promises;
  const glob = require('glob');
  
  // Clean up CSV exports
  const csvFiles = glob.sync(path.join(__dirname, '..', '..', '..', 'arrangement_*.csv'));
  for (const file of csvFiles) {
    try {
      await fs.unlink(file);
    } catch (error) {
      // Ignore errors
    }
  }
}

/**
 * Cleanup Electron app and processes
 * @param {ElectronApplication} app - Electron app instance
 * @returns {Promise<void>}
 */
async function cleanupElectronApp(app) {
  if (!app) return;
  
  try {
    // Close the app with a timeout
    await Promise.race([
      app.close(),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Close timeout')), 10000))
    ]);
    console.log('App closed successfully');
  } catch (error) {
    console.warn('App close timeout or error:', error.message);
  }
  
  // Give processes time to clean up
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Force kill any remaining backend processes on Windows
  if (process.platform === 'win32') {
    try {
      const { execSync } = require('child_process');
      execSync('taskkill /F /IM vibebells-backend.exe /T 2>nul', { stdio: 'ignore' });
      console.log('Cleaned up any remaining backend processes');
    } catch (error) {
      // Process may not exist, ignore error
    }
  }
}

/**
 * Take screenshot for debugging
 * @param {Page} window - Playwright page object
 * @param {string} name - Screenshot name
 * @returns {Promise<void>}
 */
async function takeScreenshot(window, name) {
  const screenshotPath = path.join(__dirname, '..', 'screenshots', `${name}-${Date.now()}.png`);
  await window.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`Screenshot saved: ${screenshotPath}`);
}

module.exports = {
  launchElectronApp,
  waitForBackend,
  waitForFrontend,
  uploadMidiFile,
  generateArrangements,
  cleanupTestArtifacts,
  cleanupElectronApp,
  takeScreenshot
};
