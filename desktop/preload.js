const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // Dialog APIs
  openFileDialog: () => ipcRenderer.invoke('dialog:openFile'),
  saveFileDialog: (defaultName) => ipcRenderer.invoke('dialog:saveFile', defaultName),
  
  // File system operations
  readFile: (filePath) => ipcRenderer.invoke('fs:readFile', filePath),
  
  // App info
  getVersion: () => ipcRenderer.invoke('app:getVersion'),
  
  // Check if running in Electron
  isElectron: true,
  
  // Menu event listeners with cleanup support
  onMenuOpenFile: (callback) => {
    const handler = () => callback();
    ipcRenderer.on('menu-open-file', handler);
    // Return cleanup function
    return () => ipcRenderer.removeListener('menu-open-file', handler);
  },
  onMenuExportCSV: (callback) => {
    const handler = () => callback();
    ipcRenderer.on('menu-export-csv', handler);
    // Return cleanup function
    return () => ipcRenderer.removeListener('menu-export-csv', handler);
  }
});
