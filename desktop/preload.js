const { contextBridge, ipcRenderer } = require('electron');

// Mock registry for tests (mutable, not exposed through contextBridge)
const mockRegistry = {};

// Expose the Electron API
contextBridge.exposeInMainWorld('electron', {
  // Dialog APIs - check for mocks first
  openFileDialog: () => {
    if (mockRegistry.openFileDialog) {
      return mockRegistry.openFileDialog();
    }
    return ipcRenderer.invoke('dialog:openFile');
  },
  
  saveFileDialog: (defaultName) => {
    if (mockRegistry.saveFileDialog) {
      return mockRegistry.saveFileDialog(defaultName);
    }
    return ipcRenderer.invoke('dialog:saveFile', defaultName);
  },
  
  // File system operations - check for mocks first
  readFile: (filePath) => {
    if (mockRegistry.readFile) {
      return mockRegistry.readFile(filePath);
    }
    return ipcRenderer.invoke('fs:readFile', filePath);
  },
  
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
});

// Expose helpers for tests to set/clear mocks, but only in test/E2E environments
if (process.env.NODE_ENV === 'test' || process.env.E2E_TEST === 'true') {
  contextBridge.exposeInMainWorld('__setElectronMock', (methodName, mockFn) => {
    mockRegistry[methodName] = mockFn;
    return true;
  });

  contextBridge.exposeInMainWorld('__clearElectronMocks', () => {
    Object.keys(mockRegistry).forEach(key => delete mockRegistry[key]);
  });
}
