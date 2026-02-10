// Electron integration utilities

/**
 * @typedef {Object} ElectronAPI
 * @property {() => Promise<string|null>} openFileDialog - Open file dialog for MIDI files
 * @property {(defaultName: string) => Promise<string|null>} saveFileDialog - Save file dialog for CSV export
 * @property {(filePath: string) => Promise<{success: boolean, data?: number[], error?: string}>} readFile - Read file contents
 * @property {() => Promise<string>} getVersion - Get Electron app version
 * @property {boolean} isElectron - Flag indicating if running in Electron
 * @property {(callback: () => void) => (() => void)} onMenuOpenFile - Register handler for File > Open menu, returns cleanup function
 * @property {(callback: () => void) => (() => void)} onMenuExportCSV - Register handler for File > Export menu, returns cleanup function
 */

/**
 * Check if the app is running in Electron
 * @returns {boolean} True if running in Electron, false if in browser
 */
export const isElectron = () => {
  return typeof window !== 'undefined' && window.electron && window.electron.isElectron;
};

/**
 * Open native file dialog for MIDI files
 * @returns {Promise<string|null>} Selected file path or null if cancelled
 */
export const openFileDialog = async () => {
  if (isElectron()) {
    return await window.electron.openFileDialog();
  }
  return null;
};

/**
 * Open native save dialog for CSV export
 * @param {string} defaultName - Default filename for the save dialog
 * @returns {Promise<string|null>} Selected file path or null if cancelled
 */
export const saveFileDialog = async (defaultName) => {
  if (isElectron()) {
    return await window.electron.saveFileDialog(defaultName);
  }
  return null;
};

/**
 * Read file contents through IPC (secure file access)
 * @param {string} filePath - Path to file to read
 * @returns {Promise<{success: boolean, data?: number[], error?: string}>} File contents as byte array or error
 */
export const readFile = async (filePath) => {
  if (isElectron()) {
    return await window.electron.readFile(filePath);
  }
  return { success: false, error: 'Not running in Electron' };
};

/**
 * Get the Electron application version
 * @returns {Promise<string|null>} App version or null if not in Electron
 */
export const getVersion = async () => {
  if (isElectron()) {
    return await window.electron.getVersion();
  }
  return null;
};

// Backwards-compatible alias for existing callers
export const getAppVersion = getVersion;

/**
 * Register callback for File > Open menu event
 * @param {() => void} callback - Function to call when menu item clicked
 * @returns {(() => void) | null} Cleanup function to remove listener, or null if not in Electron
 */
export const onMenuOpenFile = (callback) => {
  if (isElectron() && window.electron.onMenuOpenFile) {
    return window.electron.onMenuOpenFile(callback);
  }
  return null;
};

/**
 * Register callback for File > Export CSV menu event
 * @param {() => void} callback - Function to call when menu item clicked
 * @returns {(() => void) | null} Cleanup function to remove listener, or null if not in Electron
 */
export const onMenuExportCSV = (callback) => {
  if (isElectron() && window.electron.onMenuExportCSV) {
    return window.electron.onMenuExportCSV(callback);
  }
  return null;
};