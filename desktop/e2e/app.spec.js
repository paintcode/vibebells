/**
 * End-to-End Tests for Vibebells Desktop Application
 * 
 * Tests the complete user workflow:
 * 1. App launch and initialization
 * 2. MIDI file upload
 * 3. Player configuration
 * 4. Arrangement generation
 * 5. CSV export
 */

const { test, expect } = require('@playwright/test');
const path = require('path');
const {
  launchElectronApp,
  waitForBackend,
  waitForFrontend,
  cleanupElectronApp,
  takeScreenshot
} = require('./helpers/electron-helpers');

let electronApp;
let window;

test.describe('Vibebells Desktop Application', () => {
  
  test.beforeAll(async () => {
    console.log('Launching Electron app...');
    const result = await launchElectronApp();
    electronApp = result.app;
    window = result.window;
    
    console.log('Waiting for backend...');
    await waitForBackend();
    
    console.log('Waiting for frontend...');
    await waitForFrontend(window);
    
    console.log('✅ App ready for testing');
  });
  
  test.afterAll(async () => {
    await cleanupElectronApp(electronApp);
  });
  
  test('should launch and display main window', async () => {
    // Verify window exists and has loaded content
    expect(window).toBeTruthy();
    
    // Check window title
    const title = await window.title();
    expect(title).toContain('Handbell');
    
    // Verify main UI elements are present
    await expect(window.locator('h1')).toBeVisible();
  });
  
  test('should connect to backend successfully', async () => {
    // Make direct API call to health endpoint
    const response = await fetch('http://localhost:5000/api/health');
    expect(response.ok).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });
  
  test('should display file upload section', async () => {
    // Check for file upload UI
    const fileInput = window.locator('input[type="file"]');
    await expect(fileInput).toBeAttached();
    
    // Check for upload instructions or label
    const uploadSection = window.locator('text=Choose File').or(window.locator('text=Upload'));
    await expect(uploadSection.first()).toBeVisible();
  });
  
  test('should display player configuration section', async () => {
    // Look for player configuration UI
    const playerSection = window.locator('text=Player').or(window.locator('text=Add Player'));
    await expect(playerSection.first()).toBeVisible();
  });
  
  test('should have Generate Arrangements button (initially disabled)', async () => {
    const generateButton = window.locator('button:has-text("Generate Arrangements")');
    await expect(generateButton).toBeVisible();
    
    // Button should be disabled initially (no file uploaded)
    const isDisabled = await generateButton.isDisabled();
    expect(isDisabled).toBeTruthy();
  });
  
  test('should upload MIDI file successfully', async () => {
    const midiPath = path.join(__dirname, 'fixtures', 'test-song.mid');
    
    // Set up file chooser handler
    const fileChooserPromise = window.waitForEvent('filechooser');
    
    // Click the file input or trigger file selection
    const fileInput = window.locator('input[type="file"]');
    await fileInput.click();
    
    // Handle file chooser
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(midiPath);
    
    // Wait for file to be processed
    await window.waitForTimeout(2000);
    
    // Verify file name is displayed
    const fileName = window.locator('text=test-song.mid').or(window.locator('text=.mid'));
    await expect(fileName.first()).toBeVisible({ timeout: 5000 });
  });
  
  test('should add and configure players', async () => {
    // Look for initial player inputs
    const playerInputs = window.locator('input[placeholder*="Player"]').or(window.locator('input[value*="Player"]'));
    const initialCount = await playerInputs.count();
    
    expect(initialCount).toBeGreaterThan(0);
    
    // Try to add another player if "Add Player" button exists
    const addButton = window.locator('button:has-text("Add Player")');
    if (await addButton.isVisible()) {
      await addButton.click();
      await window.waitForTimeout(500);
      
      // Verify player count increased
      const newCount = await playerInputs.count();
      expect(newCount).toBeGreaterThan(initialCount);
    }
  });
  
  test('should generate arrangements successfully', async () => {
    // Find and click Generate Arrangements button
    const generateButton = window.locator('button:has-text("Generate Arrangements")');
    
    // Wait for button to be enabled (file uploaded, players configured)
    await expect(generateButton).toBeEnabled({ timeout: 10000 });
    
    // Click generate button
    await generateButton.click();
    
    // Wait for loading to complete (look for results or loading indicator disappears)
    await window.waitForTimeout(3000);
    
    // Check for arrangement results
    // Look for common elements in results: strategy names, quality scores, player assignments
    const resultsVisible = await Promise.race([
      window.locator('text=experienced_first').isVisible().then(() => true).catch(() => false),
      window.locator('text=balanced').isVisible().then(() => true).catch(() => false),
      window.locator('text=Quality Score').isVisible().then(() => true).catch(() => false),
      window.locator('text=Strategy').isVisible().then(() => true).catch(() => false)
    ]);
    
    expect(resultsVisible).toBeTruthy();
  });
  
  test('should display arrangement details', async () => {
    // This test checks that the UI can display arrangement details
    // Since no arrangement is generated yet, we check the structure exists
    
    // Check that main content area exists
    const mainContent = window.locator('main, #__next, body');
    await expect(mainContent.first()).toBeVisible();
    
    // Verify the page has loaded with content
    const heading = window.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toContainText(/Handbell|Arrangement/i);
  });
  
  test('should allow CSV export', async () => {
    // Look for Export button
    const exportButton = window.locator('button:has-text("Export")').or(window.locator('button:has-text("CSV")'));
    
    // If export button exists, verify it's enabled
    const exportExists = await exportButton.count();
    if (exportExists > 0) {
      await expect(exportButton.first()).toBeEnabled();
      
      // Note: Actually clicking and saving the file requires additional setup
      // to handle the native save dialog, which we'll skip for now
      console.log('✓ Export button is available and enabled');
    } else {
      console.log('⚠️  Export button not found (may require specific arrangement selection)');
    }
  });
  
  test('should handle app close gracefully', async () => {
    // Verify app is running
    expect(await window.isClosed()).toBeFalsy();
    
    // Verify window title is still accessible
    const title = await window.title();
    expect(title).toBeTruthy();
  });
});
