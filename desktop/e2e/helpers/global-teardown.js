/**
 * Global teardown for E2E tests
 */

const { cleanupTestArtifacts } = require('./electron-helpers');

module.exports = async () => {
  console.log('\n🧹 E2E Test Suite - Global Teardown');
  console.log('Cleaning up test artifacts...');
  
  try {
    await cleanupTestArtifacts();
    console.log('✅ Cleanup complete');
  } catch (error) {
    console.error('⚠️  Cleanup error:', error.message);
  }
};
