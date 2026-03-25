import http from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, '..');
const dataPath = path.join(root, 'app', 'data', 'state.json');
const publicDir = path.join(root, 'app', 'public');

function sendJson(res, status, data) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(data, null, 2));
}

function sendText(res, status, text, contentType = 'text/plain; charset=utf-8') {
  res.writeHead(status, { 'Content-Type': contentType });
  res.end(text);
}

async function loadState() {
  const raw = await readFile(dataPath, 'utf8');
  return JSON.parse(raw);
}

async function saveState(state) {
  state.meta.updatedAt = new Date().toISOString();
  await writeFile(dataPath, JSON.stringify(state, null, 2) + '\n', 'utf8');
}

async function serveFile(res, filePath, contentType) {
  try {
    const data = await readFile(filePath);
    sendText(res, 200, data, contentType);
  } catch {
    sendText(res, 404, 'Not found');
  }
}

function collectBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', chunk => {
      data += chunk;
      if (data.length > 1_000_000) {
        reject(new Error('Body too large'));
        req.destroy();
      }
    });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');

  if (req.method === 'GET' && url.pathname === '/api/state') {
    const state = await loadState();
    return sendJson(res, 200, state);
  }

  if (req.method === 'POST' && url.pathname === '/api/activity') {
    try {
      const state = await loadState();
      const body = JSON.parse(await collectBody(req));
      const entry = {
        id: body.id || `activity-${Date.now()}`,
        type: body.type || 'note',
        message: body.message || 'Updated activity log.',
        timestamp: new Date().toISOString()
      };
      state.activity.unshift(entry);
      await saveState(state);
      return sendJson(res, 200, { ok: true, entry });
    } catch (error) {
      return sendJson(res, 400, { ok: false, error: error.message });
    }
  }

  if (req.method === 'POST' && url.pathname === '/api/tasks') {
    try {
      const state = await loadState();
      const body = JSON.parse(await collectBody(req));
      const task = {
        id: body.id || `task-${Date.now()}`,
        projectId: body.projectId || 'unassigned',
        title: body.title || 'Untitled task',
        status: body.status || 'backlog',
        priority: body.priority || 'normal',
        owner: body.owner || 'Clawdbot',
        notes: body.notes || '',
        updatedAt: new Date().toISOString()
      };
      state.tasks.unshift(task);
      state.activity.unshift({
        id: `activity-${Date.now()}`,
        type: 'task_created',
        message: `Created task: ${task.title}`,
        timestamp: new Date().toISOString()
      });
      await saveState(state);
      return sendJson(res, 200, { ok: true, task });
    } catch (error) {
      return sendJson(res, 400, { ok: false, error: error.message });
    }
  }

  if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/index.html')) {
    return serveFile(res, path.join(publicDir, 'index.html'), 'text/html; charset=utf-8');
  }

  if (req.method === 'GET' && url.pathname === '/styles.css') {
    return serveFile(res, path.join(publicDir, 'styles.css'), 'text/css; charset=utf-8');
  }

  if (req.method === 'GET' && url.pathname === '/app.js') {
    return serveFile(res, path.join(publicDir, 'app.js'), 'text/javascript; charset=utf-8');
  }

  sendText(res, 404, 'Not found');
});

const port = Number(process.env.PORT || 4317);
server.listen(port, '0.0.0.0', () => {
  console.log(`Clawdbot Console running on http://0.0.0.0:${port}`);
});
