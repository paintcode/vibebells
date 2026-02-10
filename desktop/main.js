const { app, BrowserWindow, Menu, dialog, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const log = require('electron-log');
const http = require('http');
const { readFile } = require('fs/promises');

// Configure logging
log.transports.file.level = 'info';
log.transports.console.level = 'debug';
log.info('Application starting...');

let mainWindow = null;
let pythonProcess = null;
let frontendServer = null;

const isDev = process.env.NODE_ENV === 'development';

// Configuration constants
const BACKEND_PORT = process.env.BACKEND_PORT || 5000;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;
const FRONTEND_PORT = 3001; // Use different port from backend
const HEALTH_CHECK_DELAY_MS = 2000;
const HEALTH_CHECK_INTERVAL_MS = 1000;
const MAX_HEALTH_CHECK_ATTEMPTS = 30;

// Validate file path is not a system directory
function isValidFilePath(filePath) {
  if (!filePath) return false;
  
  const normalizedPath = path.normalize(filePath).toLowerCase();
  const systemPaths = [
    'system32',
    'windows',
    'program files',
    'programdata',
    '/system/',
    '/library/system',
    '/bin/',
    '/sbin/'
  ];
  
  return !systemPaths.some(sysPath => normalizedPath.includes(sysPath));
}

// Start Python backend
function startBackend() {
  return new Promise((resolve, reject) => {
    log.info('Starting Python backend...');
    
    // Capture stderr output for error reporting
    let stderrOutput = '';
    
    if (isDev) {
      // Development: Use Python from system
      const backendPath = path.join(__dirname, '..', 'backend');
      pythonProcess = spawn('python', ['-m', 'flask', 'run'], {
        cwd: backendPath,
        env: { ...process.env, FLASK_ENV: 'production', FLASK_APP: 'app' }
        // Removed shell: true for security
      });
    } else {
      // Production: Use bundled Python executable
      const pythonExe = path.join(
        process.resourcesPath,
        'backend',
        process.platform === 'win32' ? 'vibebells-backend.exe' : 'vibebells-backend'
      );
      
      // Validate backend executable exists and is accessible
      if (!fs.existsSync(pythonExe)) {
        const errorMsg = `Python backend not found at ${pythonExe}. Please ensure the application was built correctly.`;
        log.error(errorMsg);
        reject(new Error(errorMsg));
        return;
      }
      
      // Verify it's a file and not a directory
      const stats = fs.statSync(pythonExe);
      if (!stats.isFile()) {
        const errorMsg = `Backend path exists but is not a file: ${pythonExe}`;
        log.error(errorMsg);
        reject(new Error(errorMsg));
        return;
      }
      
      log.info(`Using bundled Python backend: ${pythonExe}`);
      pythonProcess = spawn(pythonExe, [], {
        env: { ...process.env, FLASK_ENV: 'production' }
      });
    }
    
    pythonProcess.stdout.on('data', (data) => {
      log.info(`Backend: ${data}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      const errorText = data.toString();
      log.error(`Backend Error: ${errorText}`);
      // Accumulate stderr for error reporting
      stderrOutput += errorText;
      // Keep only last 500 characters to avoid memory issues
      if (stderrOutput.length > 500) {
        stderrOutput = stderrOutput.slice(-500);
      }
    });
    
    pythonProcess.on('error', (error) => {
      log.error('Failed to start Python backend:', error);
      // Clean up process on error to prevent resource leak
      if (pythonProcess) {
        pythonProcess.kill();
        pythonProcess = null;
      }
      // Include stderr output in error message
      const fullError = stderrOutput 
        ? `${error.message}\n\nBackend stderr:\n${stderrOutput}`
        : error.message;
      reject(new Error(fullError));
    });
    
    pythonProcess.on('exit', (code, signal) => {
      log.info(`Backend exited with code ${code} and signal ${signal}`);
      // If exit happens during startup, include stderr in error
      if (code !== 0 && code !== null) {
        const exitError = `Backend process exited with code ${code}`;
        const fullError = stderrOutput 
          ? `${exitError}\n\nBackend stderr:\n${stderrOutput}`
          : exitError;
        reject(new Error(fullError));
      }
    });
    
    // Wait for backend to be ready (poll health endpoint)
    let attempts = 0;
    let lastError = null;
    
    const checkHealth = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/health`);
        if (response.ok) {
          log.info('Backend is ready!');
          resolve();
        } else {
          lastError = `Backend responded with status ${response.status}`;
          throw new Error('Backend not ready');
        }
      } catch (error) {
        lastError = error.message;
        attempts++;
        log.info(`Health check attempt ${attempts}/${MAX_HEALTH_CHECK_ATTEMPTS} failed: ${error.message}`);
        
        if (attempts >= MAX_HEALTH_CHECK_ATTEMPTS) {
          // Kill process before rejecting to prevent resource leak
          if (pythonProcess) {
            pythonProcess.kill();
            pythonProcess = null;
          }
          
          // Include stderr output in final error message
          let errorMessage = `Backend failed to start after ${MAX_HEALTH_CHECK_ATTEMPTS} seconds.\n\nLast error: ${lastError}`;
          if (stderrOutput) {
            errorMessage += `\n\nBackend stderr output:\n${stderrOutput}`;
          }
          
          reject(new Error(errorMessage));
        } else {
          setTimeout(checkHealth, HEALTH_CHECK_INTERVAL_MS);
        }
      }
    };
    
    // Start checking after initial delay
    setTimeout(checkHealth, HEALTH_CHECK_DELAY_MS);
  });
}

// Stop Python backend
function stopBackend() {
  if (pythonProcess) {
    log.info('Stopping Python backend...');
    pythonProcess.kill();
    pythonProcess = null;
  }
}

// Start frontend server for production
function startFrontendServer() {
  return new Promise((resolve, reject) => {
    const buildPath = path.join(__dirname, 'build');
    
    if (!fs.existsSync(buildPath)) {
      reject(new Error(`Frontend build not found at ${buildPath}`));
      return;
    }
    
    const mimeTypes = {
      '.html': 'text/html',
      '.js': 'text/javascript',
      '.css': 'text/css',
      '.json': 'application/json',
      '.png': 'image/png',
      '.jpg': 'image/jpg',
      '.gif': 'image/gif',
      '.svg': 'image/svg+xml',
      '.ico': 'image/x-icon',
      '.txt': 'text/plain'
    };
    
    frontendServer = http.createServer(async (req, res) => {
      let filePath = path.join(buildPath, req.url === '/' ? 'index.html' : req.url);
      
      // Normalize path
      filePath = path.normalize(filePath);
      
      // Security check: ensure file is within build directory
      if (!filePath.startsWith(buildPath)) {
        res.writeHead(403);
        res.end('Forbidden');
        return;
      }
      
      try {
        const ext = path.extname(filePath);
        const contentType = mimeTypes[ext] || 'application/octet-stream';
        
        const content = await readFile(filePath);
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(content);
      } catch (error) {
        if (error.code === 'ENOENT') {
          // File not found, try serving index.html for client-side routing
          try {
            const content = await readFile(path.join(buildPath, 'index.html'));
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(content);
          } catch {
            res.writeHead(404);
            res.end('Not found');
          }
        } else {
          res.writeHead(500);
          res.end('Server error');
        }
      }
    });
    
    frontendServer.on('error', (error) => {
      log.error('Frontend server error:', error);
      reject(error);
    });
    
    frontendServer.listen(FRONTEND_PORT, 'localhost', () => {
      log.info(`Frontend server listening on http://localhost:${FRONTEND_PORT}`);
      resolve();
    });
  });
}

// Stop frontend server
function stopFrontendServer() {
  if (frontendServer) {
    log.info('Stopping frontend server...');
    frontendServer.close();
    frontendServer = null;
  }
}

// Create main window
async function createWindow() {
  // Check if icon exists to avoid warning
  const iconPath = path.join(__dirname, 'assets', 'icon.png');
  const windowConfig = {
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      enableRemoteModule: false,
      webSecurity: true,
      sandbox: true
    }
  };
  
  // Only set icon if it exists
  if (fs.existsSync(iconPath)) {
    windowConfig.icon = iconPath;
  } else {
    log.warn('Application icon not found at:', iconPath);
  }
  
  mainWindow = new BrowserWindow(windowConfig);

  // Create application menu
  const menuTemplate = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open MIDI...',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            mainWindow.webContents.send('menu-open-file');
          }
        },
        {
          label: 'Export CSV...',
          accelerator: 'CmdOrCtrl+E',
          click: () => {
            mainWindow.webContents.send('menu-export-csv');
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About Vibebells',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Vibebells',
              message: 'Vibebells',
              detail: 'Handbell Arrangement Generator\nVersion 1.0.0\n\nGenerates handbell arrangements from MIDI files.',
              buttons: ['OK']
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(menuTemplate);
  Menu.setApplicationMenu(menu);

  // Start backend first
  try {
    await startBackend();
  } catch (error) {
    // Show error dialog with retry option
    const choice = dialog.showMessageBoxSync(mainWindow, {
      type: 'error',
      title: 'Backend Startup Failed',
      message: 'Failed to start the Python backend',
      detail: error.message,
      buttons: ['Retry', 'Quit'],
      defaultId: 0,
      cancelId: 1
    });
    
    if (choice === 0) {
      // User chose Retry
      log.info('Retrying backend startup...');
      return createWindow(); // Recursive retry
    } else {
      // User chose Quit
      app.quit();
      return;
    }
  }

  // Load the app
  if (isDev) {
    // Development: Load from Next.js dev server
    // Check if dev server is running first
    try {
      await fetch('http://localhost:3000');
      log.info('Next.js dev server detected, loading UI...');
      mainWindow.loadURL('http://localhost:3000');
      mainWindow.webContents.openDevTools();
    } catch (error) {
      log.error('Next.js dev server not running:', error.message);
      const choice = dialog.showMessageBoxSync(mainWindow, {
        type: 'error',
        title: 'Dev Server Not Running',
        message: 'Next.js development server is not running',
        detail: 'Start the dev server first:\n\ncd frontend\nnpm run dev\n\nThen restart Electron.',
        buttons: ['Quit', 'Try Anyway'],
        defaultId: 0
      });
      
      if (choice === 0) {
        app.quit();
        return;
      } else {
        // Try loading anyway (might succeed later)
        mainWindow.loadURL('http://localhost:3000');
        mainWindow.webContents.openDevTools();
      }
    }
  } else {
    // Production: Start frontend server and load from it
    try {
      await startFrontendServer();
      mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`);
    } catch (error) {
      log.error('Failed to start frontend server:', error);
      dialog.showErrorBox('Frontend Error', `Failed to start frontend server: ${error.message}`);
      app.quit();
      return;
    }
  }

  mainWindow.on('closed', () => {
    stopBackend(); // Explicitly stop backend on window close
    stopFrontendServer(); // Stop frontend server
    mainWindow = null;
  });
}

// IPC handlers
ipcMain.handle('dialog:openFile', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'MIDI Files', extensions: ['mid', 'midi'] }
    ]
  });
  
  if (!result.canceled && result.filePaths.length > 0) {
    const filePath = result.filePaths[0];
    
    // Validate file path for security
    if (!isValidFilePath(filePath)) {
      log.error('Rejected invalid file path:', filePath);
      dialog.showErrorBox('Invalid File Path', 'Cannot open files from system directories.');
      return null;
    }
    
    return filePath;
  }
  return null;
});

// File system operations
ipcMain.handle('fs:readFile', async (event, filePath) => {
  try {
    // Validate path before reading
    if (!isValidFilePath(filePath)) {
      log.error('Rejected invalid file path for reading:', filePath);
      return { success: false, error: 'Invalid file path' };
    }
    
    // Read file as buffer
    const data = await fs.promises.readFile(filePath);
    // Convert to array for JSON serialization
    return { success: true, data: Array.from(data) };
  } catch (error) {
    log.error('Error reading file:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('dialog:saveFile', async (event, defaultName) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: defaultName,
    filters: [
      { name: 'CSV Files', extensions: ['csv'] }
    ]
  });
  
  if (!result.canceled && result.filePath) {
    const filePath = result.filePath;
    
    // Validate file path for security
    if (!isValidFilePath(filePath)) {
      log.error('Rejected invalid save path:', filePath);
      dialog.showErrorBox('Invalid File Path', 'Cannot save files to system directories.');
      return null;
    }
    
    return filePath;
  }
  return null;
});

ipcMain.handle('app:getVersion', () => {
  return app.getVersion();
});

// App lifecycle
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  stopBackend();
  stopFrontendServer();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopBackend();
  stopFrontendServer();
});

app.on('will-quit', () => {
  stopBackend();
  stopFrontendServer();
});
