import { app, BrowserWindow } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, '..');
let serverProcess;

function startServer() {
  const serverPath = path.join(root, 'app', 'server.js');
  serverProcess = spawn(process.execPath, [serverPath], {
    cwd: root,
    stdio: 'ignore',
    env: { ...process.env, PORT: process.env.PORT || '4317' }
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 960,
    backgroundColor: '#0b1020',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true
    }
  });

  win.loadURL(`http://127.0.0.1:${process.env.PORT || '4317'}`);
}

app.whenReady().then(() => {
  startServer();
  setTimeout(createWindow, 1200);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (serverProcess) serverProcess.kill();
});
