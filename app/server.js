import http from 'node:http';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { extname, join } from 'node:path';

const PORT = process.env.PORT || 4317;
const ROOT = process.cwd();
const PUBLIC_DIR = join(ROOT, 'app', 'public');
const DATA_DIR = join(ROOT, 'app', 'data');
const STATE_PATH = join(DATA_DIR, 'state.json');

mkdirSync(DATA_DIR, { recursive: true });
mkdirSync(PUBLIC_DIR, { recursive: true });

if (!existsSync(STATE_PATH)) {
  throw new Error(`Missing state file at ${STATE_PATH}`);
}

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8'
};

function loadState() {
  return JSON.parse(readFileSync(STATE_PATH, 'utf8'));
}

function saveState(state) {
  writeFileSync(STATE_PATH, JSON.stringify(state, null, 2));
}

function json(res, code, payload) {
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(payload, null, 2));
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', chunk => {
      data += chunk;
      if (data.length > 1_000_000) {
        reject(new Error('Body too large'));
      }
    });
    req.on('end', () => {
      try {
        resolve(data ? JSON.parse(data) : {});
      } catch (error) {
        reject(error);
      }
    });
    req.on('error', reject);
  });
}

function buildOracleReply(oracle, userText) {
  return `${oracle.oracle_name} receives: “${userText}” and replies in a prototype voice. True live oracle inference remains pending provider binding.`;
}

const server = http.createServer(async (req, res) => {
  if (!req.url) {
    res.writeHead(400);
    res.end('Bad request');
    return;
  }

  if (req.method === 'GET' && req.url === '/api/state') {
    json(res, 200, loadState());
    return;
  }

  if (req.method === 'POST' && req.url === '/api/profile') {
    try {
      const body = await parseBody(req);
      const state = loadState();
      state.currentUser = { ...state.currentUser, ...body };
      state.astrologyProfile.birthData = {
        date: body.birthday ?? state.astrologyProfile.birthData.date,
        time: body.birthTime ?? state.astrologyProfile.birthData.time,
        location: body.birthLocation ?? state.astrologyProfile.birthData.location
      };
      saveState(state);
      json(res, 200, { ok: true, currentUser: state.currentUser, astrologyProfile: state.astrologyProfile });
    } catch (error) {
      json(res, 400, { ok: false, error: error.message });
    }
    return;
  }

  if (req.method === 'POST' && req.url === '/api/provider') {
    try {
      const body = await parseBody(req);
      const state = loadState();
      const provider = state.providers.find(p => p.id === body.id) || state.providers[0];
      provider.baseUrl = body.baseUrl ?? provider.baseUrl;
      provider.model = body.model ?? provider.model;
      provider.apiKeyStatus = body.apiKey ? 'configured' : provider.apiKeyStatus;
      provider.ready = Boolean(provider.baseUrl && provider.model && provider.apiKeyStatus === 'configured');
      state.sessions = state.sessions.map(session => session.providerId === provider.id ? { ...session, model: provider.model, providerReady: provider.ready } : session);
      saveState(state);
      json(res, 200, { ok: true, provider });
    } catch (error) {
      json(res, 400, { ok: false, error: error.message });
    }
    return;
  }

  if (req.method === 'POST' && req.url === '/api/oracles') {
    try {
      const body = await parseBody(req);
      const state = loadState();
      const oracleId = body.oracle_id || `oracle-${String(body.oracle_name || 'oracle').toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
      const oracle = {
        oracle_id: oracleId,
        oracle_name: body.oracle_name || 'Unnamed Oracle',
        title: body.title || '',
        archetype: body.archetype || '',
        ruling_planet: body.ruling_planet || '',
        dominant_sign: body.dominant_sign || '',
        house_placement: body.house_placement || '',
        aspects: [],
        transit_modifiers: [],
        voice: body.voice || '',
        faction: body.faction || '',
        planetary_faction: body.planetary_faction || '',
        role: body.role || '',
        weapon: body.weapon || '',
        color_scheme: body.color_scheme || '',
        silhouette: body.silhouette || '',
        spirit_animal: body.spirit_animal || '',
        combat_style: body.combat_style || '',
        guidance_style: body.guidance_style || '',
        relationship_mode: body.relationship_mode || '',
        mission: body.mission || '',
        notes: body.notes || ''
      };
      state.oracles.push(oracle);
      state.sessions.push({
        id: `session-${oracleId}`,
        oracleId,
        providerId: state.providers[0]?.id || 'default-provider',
        model: state.providers[0]?.model || '',
        providerReady: state.providers[0]?.ready || false,
        messages: [
          { role: 'oracle', text: `${oracle.oracle_name} enters the chamber. The awakening is complete enough for prototype interaction.` }
        ]
      });
      saveState(state);
      json(res, 200, { ok: true, oracle });
    } catch (error) {
      json(res, 400, { ok: false, error: error.message });
    }
    return;
  }

  if (req.method === 'POST' && req.url === '/api/session-message') {
    try {
      const body = await parseBody(req);
      const state = loadState();
      const session = state.sessions.find(s => s.id === body.sessionId);
      if (!session) {
        json(res, 404, { ok: false, error: 'Session not found' });
        return;
      }
      const oracle = state.oracles.find(o => o.oracle_id === session.oracleId);
      session.messages.push({ role: 'user', text: body.text || '' });
      session.messages.push({ role: 'oracle', text: buildOracleReply(oracle, body.text || '') });
      saveState(state);
      json(res, 200, { ok: true, session });
    } catch (error) {
      json(res, 400, { ok: false, error: error.message });
    }
    return;
  }

  if (req.method === 'POST' && req.url === '/api/oracle-draft') {
    try {
      const body = await parseBody(req);
      const state = loadState();
      const draft = {
        id: `draft-${Date.now()}`,
        oracleId: body.oracleId,
        message: body.message || '',
        type: body.type || 'draft'
      };
      state.oracleDrafts.unshift(draft);
      saveState(state);
      json(res, 200, { ok: true, draft });
    } catch (error) {
      json(res, 400, { ok: false, error: error.message });
    }
    return;
  }

  if (req.method === 'POST' && req.url === '/api/oracle-note') {
    try {
      const body = await parseBody(req);
      const state = loadState();
      const oracle = state.oracles.find(o => o.oracle_id === body.oracleId);
      if (!oracle) {
        json(res, 404, { ok: false, error: 'Oracle not found' });
        return;
      }
      oracle.notes = [oracle.notes, body.message].filter(Boolean).join(' | ');
      saveState(state);
      json(res, 200, { ok: true, oracle });
    } catch (error) {
      json(res, 400, { ok: false, error: error.message });
    }
    return;
  }

  const path = req.url === '/' ? '/index.html' : req.url;
  const filePath = join(PUBLIC_DIR, path);

  try {
    const body = readFileSync(filePath);
    res.writeHead(200, { 'Content-Type': mime[extname(filePath)] || 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Not found');
  }
});

server.listen(PORT, () => {
  console.log(`Pantheon of Oracles prototype running on http://localhost:${PORT}`);
});