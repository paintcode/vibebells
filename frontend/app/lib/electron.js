// Electron integration utilities

/**
 * @typedef {Object} ElectronAPI
 * @property {() => Promise<string|null>} openFileDialog - Open file dialog for MIDI files
 * @property {(defaultName: string) => Promise<string|null>} saveFileDialog - Save file dialog for CSV export
 * @property {() => Promise<string>} getVersion - Get Electron app version
 * @property {boolean} isElectron - Flag indicating if running in Electron
 * @property {(callback: () => void) => void} onMenuOpenFile - Register handler for File > Open menu
 * @property {(callback: () => void) => void} onMenuExportCSV - Register handler for File > Export menu
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
 * Get the Electron application version
 * @returns {Promise<string|null>} App version or null if not in Electron
 */
export const getAppVersion = async () => {
  if (isElectron()) {
    return await window.electron.getVersion();
  }
  return null;
};

/**
 * Register callback for File > Open menu event
 * @param {() => void} callback - Function to call when menu item clicked
 */
export const onMenuOpenFile = (callback) => {
  if (isElectron() && window.electron.onMenuOpenFile) {
    window.electron.onMenuOpenFile(callback);
  }
};

/**
 * Register callback for File > Export CSV menu event
 * @param {() => void} callback - Function to call when menu item clicked
 */
export const onMenuExportCSV = (callback) => {
  if (isElectron() && window.electron.onMenuExportCSV) {
    window.electron.onMenuExportCSV(callback);
  }
};