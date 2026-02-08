const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // Dialog APIs
  openFileDialog: () => ipcRenderer.invoke('dialog:openFile'),
  saveFileDialog: (defaultName) => ipcRenderer.invoke('dialog:saveFile', defaultName),
  
  // App info
  getVersion: () => ipcRenderer.invoke('app:getVersion'),
  
  // Check if running in Electron
  isElectron: true,
  
  // Menu event listeners
  onMenuOpenFile: (callback) => {
    ipcRenderer.on('menu-open-file', callback);
  },
  onMenuExportCSV: (callback) => {
    ipcRenderer.on('menu-export-csv', callback);
  }
});
