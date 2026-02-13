/**
 * Global setup for E2E tests
 */

module.exports = async () => {
  console.log('🔧 E2E Test Suite - Global Setup');
  console.log('Setting up test environment...');
  
  // Ensure screenshots directory exists
  const fs = require('fs');
  const path = require('path');
  const screenshotsDir = path.join(__dirname, '..', 'screenshots');
  
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }
  
  console.log('✅ Global setup complete\n');
};
