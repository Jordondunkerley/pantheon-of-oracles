import { app, BrowserWindow } from 'electron';
import { spawn } from 'node:child_process';
import { join } from 'node:path';

let mainWindow;
let serverProcess;

function startServer() {
  const cwd = process.cwd();
  serverProcess = spawn(process.execPath, [join(cwd, 'app', 'server.js')], {
    cwd,
    stdio: 'ignore'
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1100,
    minHeight: 760,
    backgroundColor: '#0a0b12',
    title: 'Pantheon of Oracles: The Council Chamber'
  });

  mainWindow.loadURL('http://127.0.0.1:4317');
}

app.whenReady().then(() => {
  startServer();
  setTimeout(createWindow, 1200);
});

app.on('window-all-closed', () => {
  if (serverProcess) serverProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});