const { contextBridge, ipcRenderer } = require('electron');

// Create mutable test API that can be mocked
const electronAPI = {
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
    return () => ipcRenderer.removeListener('menu-open-file', handler);
  },
  onMenuExportCSV: (callback) => {
    const handler = () => callback();
    ipcRenderer.on('menu-export-csv', handler);
    return () => ipcRenderer.removeListener('menu-export-csv', handler);
  }
};

// Expose the API
contextBridge.exposeInMainWorld('electron', electronAPI);

// Expose helper for tests to override methods (always available, but only used in tests)
contextBridge.exposeInMainWorld('__setElectronMock', (methodName, mockFn) => {
  if (electronAPI.hasOwnProperty(methodName)) {
    electronAPI[methodName] = mockFn;
    return true;
  }
  return false;
});
