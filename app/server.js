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
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
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

function stampActivity(state, type, message) {
  state.activity.unshift({
    id: `activity-${Date.now()}`,
    type,
    message,
    timestamp: new Date().toISOString()
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');

  if (req.method === 'GET' && url.pathname === '/api/state') {
    const state = await loadState();
    return sendJson(res, 200, state);
  }

  if (req.method === 'POST' && url.pathname === '/api/current-user') {
    try {
      const state = await loadState();
      const body = JSON.parse(await collectBody(req));
      state.currentUser = {
        ...state.currentUser,
        username: body.username ?? state.currentUser.username,
        email: body.email ?? state.currentUser.email,
        gender: body.gender ?? state.currentUser.gender,
        birthday: body.birthday ?? state.currentUser.birthday,
        birth_time: body.birth_time ?? state.currentUser.birth_time,
        birth_location: body.birth_location ?? state.currentUser.birth_location,
        preferences: {
          ...state.currentUser.preferences,
          oracle_voice_flavor: body.oracle_voice_flavor ?? state.currentUser.preferences.oracle_voice_flavor,
          system_prompt_tone: body.system_prompt_tone ?? state.currentUser.preferences.system_prompt_tone
        }
      };
      stampActivity(state, 'profile_updated', 'Updated current user profile for Pantheon onboarding.');
      await saveState(state);
      return sendJson(res, 200, { ok: true, currentUser: state.currentUser });
    } catch (error) {
      return sendJson(res, 400, { ok: false, error: error.message });
    }
  }

  if (req.method === 'POST' && url.pathname === '/api/chart/generate') {
    try {
      const state = await loadState();
      stampActivity(state, 'chart_generation', 'Triggered chart generation flow from birth data. This prototype still uses seeded astrology data while native chart generation is being prepared.');
      await saveState(state);
      return sendJson(res, 200, {
        ok: true,
        mode: 'prototype-seeded',
        message: 'Chart generation flow triggered. Native calculation and external validation path will plug into this endpoint.'
      });
    } catch (error) {
      return sendJson(res, 400, { ok: false, error: error.message });
    }
  }

  if (req.method === 'POST' && url.pathname === '/api/providers') {
    try {
      const state = await loadState();
      const body = JSON.parse(await collectBody(req));
      const provider = state.llmProviders.find(item => item.id === body.id);
      if (!provider) return sendJson(res, 404, { ok: false, error: 'Provider not found' });
      provider.baseUrl = body.baseUrl ?? provider.baseUrl ?? '';
      provider.model = body.model ?? provider.model ?? '';
      provider.apiKeyStatus = body.apiKey ? 'provided' : (provider.apiKeyStatus || 'missing');
      provider.enabled = body.enabled ?? provider.enabled;
      state.interactionSessions = state.interactionSessions.map(session => session.providerId === provider.id
        ? { ...session, model: provider.model || session.model || '', providerReady: Boolean(provider.enabled && provider.model && provider.apiKeyStatus === 'provided') }
        : session);
      stampActivity(state, 'provider_updated', `Updated provider configuration: ${provider.name}`);
      await saveState(state);
      return sendJson(res, 200, { ok: true, provider });
    } catch (error) {
      return sendJson(res, 400, { ok: false, error: error.message });
    }
  }

  if (req.method === 'POST' && url.pathname === '/api/oracle-voice') {
    try {
      const state = await loadState();
      const body = JSON.parse(await collectBody(req));
      const oracle = state.oracles.find(item => item.oracle_id === body.oracleId);
      if (!oracle) return sendJson(res, 404, { ok: false, error: 'Oracle not found' });
      oracle.visual_attributes = oracle.visual_attributes || {};
      oracle.visual_attributes.preferred_voice_profile = body.preferredVoiceProfile ?? oracle.visual_attributes.preferred_voice_profile ?? '';
      oracle.visual_attributes.audio_ready = body.audioReady ?? oracle.visual_attributes.audio_ready ?? false;
      oracle.oracle_metadata_last_updated = new Date().toISOString();
      stampActivity(state, 'voice_updated', `Updated voice settings for ${oracle.oracle_name}`);
      await saveState(state);
      return sendJson(res, 200, { ok: true, oracle });
    } catch (error) {
      return sendJson(res, 400, { ok: false, error: error.message });
    }
  }

  if (req.method === 'POST' && url.pathname === '/api/sessions/message') {
    try {
      const state = await loadState();
      const body = JSON.parse(await collectBody(req));
      const session = state.interactionSessions.find(item => item.id === body.sessionId);
      if (!session) return sendJson(res, 404, { ok: false, error: 'Session not found' });
      if (!session.messages) session.messages = [];
      const userMessage = {
        role: 'user',
        content: body.message || '',
        timestamp: new Date().toISOString()
      };
      session.messages.push(userMessage);
      session.lastMessageAt = userMessage.timestamp;

      const oracle = state.oracles.find(item => item.oracle_id === session.oracleId);
      const provider = state.llmProviders.find(item => item.id === session.providerId);
      session.model = provider?.model || session.model || '';
      session.providerReady = Boolean(provider?.enabled && provider?.model && provider?.apiKeyStatus === 'provided');
      const oracleReply = {
        role: 'oracle',
        content: oracle
          ? `${oracle.oracle_name}: I am present. ${session.providerReady ? `Your session is now bound to ${provider?.name || 'the configured provider'} using ${session.model || 'the selected model'}.` : `This session still needs a fully configured provider before true oracle generation can begin.`}`
          : 'Oracle session active.',
        timestamp: new Date().toISOString()
      };
      session.messages.push(oracleReply);
      session.lastMessageAt = oracleReply.timestamp;
      stampActivity(state, 'oracle_session', `Sent a message in ${session.title}`);
      await saveState(state);
      return sendJson(res, 200, { ok: true, session });
    } catch (error) {
      return sendJson(res, 400, { ok: false, error: error.message });
    }
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
      stampActivity(state, 'task_created', `Created task: ${task.title}`);
      await saveState(state);
      return sendJson(res, 200, { ok: true, task });
    } catch (error) {
      return sendJson(res, 400, { ok: false, error: error.message });
    }
  }

  if (req.method === 'POST' && url.pathname === '/api/oracle-note') {
    try {
      const state = await loadState();
      const body = JSON.parse(await collectBody(req));
      const oracle = state.oracles.find(item => item.oracle_id === body.oracleId || item.id === body.oracleId);
      if (!oracle) return sendJson(res, 404, { ok: false, error: 'Oracle not found' });
      oracle.lastContact = new Date().toISOString();
      const existingNotes = oracle.visual_attributes?.additional_notes || oracle.notes || '';
      if (oracle.visual_attributes) {
        oracle.visual_attributes.additional_notes = [existingNotes, body.message].filter(Boolean).join(' | ');
      } else {
        oracle.notes = [existingNotes, body.message].filter(Boolean).join(' | ');
      }
      oracle.oracle_metadata_last_updated = new Date().toISOString();
      stampActivity(state, 'oracle_note', `Logged oracle note for ${oracle.oracle_name || oracle.name}`);
      await saveState(state);
      return sendJson(res, 200, { ok: true, oracle });
    } catch (error) {
      return sendJson(res, 400, { ok: false, error: error.message });
    }
  }

  if (req.method === 'POST' && url.pathname === '/api/oracles') {
    try {
      const state = await loadState();
      const body = JSON.parse(await collectBody(req));
      const now = new Date().toISOString();
      const oracle = {
        oracle_id: body.oracle_id || `oracle-${Date.now()}`,
        oracle_name: body.name || body.oracle_name || 'Unnamed Oracle',
        archetype: body.archetype || 'Unformed Oracle',
        oracle_type: body.oracle_type || 'Playable',
        astrology_profile: {
          ruling_planet: body.ruling_planet || '',
          dominant_sign: body.dominant_sign || '',
          house_placement: body.house_placement || '',
          motion: body.motion || 'Direct',
          stationary: body.stationary || '',
          shadow: body.shadow || '',
          degree: body.degree || '',
          degree_mark: body.degree_mark || '',
          decan: {
            method: body.decan_method || 'Modern',
            decan_ruler: body.decan_ruler || '',
            decan_ruler_sign: body.decan_ruler_sign || '',
            flavor: body.decan_flavor || 'Full'
          },
          rising_sign: body.rising_sign || '',
          rising_decan_sign: body.rising_decan_sign || ''
        },
        faction_affiliation: {
          core_faction: body.core_faction || '',
          planetary_faction: body.planetary_faction || '',
          tribe: body.tribe || '',
          guild: body.guild || ''
        },
        hardcore_status: body.hardcore_status ?? true,
        level: body.level || 0,
        tier: body.tier || 'Tier 1',
        ascended_rank: body.ascended_rank || 0,
        oracle_form: body.oracle_form || 'Base',
        council_type: body.council_type || 'Unassigned',
        descendant_relationship_state: body.descendant_relationship_state || 'Dormant',
        oracle_locked: false,
        oracle_voice: body.voice || body.oracle_voice || 'Undefined',
        tone_overlay: body.tone_overlay || body.mission || '',
        oracle_metadata_last_updated: now,
        anointed_ruler: false,
        modern_ruler: false,
        traditional_ruler: false,
        dominant_ruler: false,
        solar_ruler: false,
        has_shapeshift: false,
        shapeshift_description: '',
        has_pet: false,
        pet_name: '',
        pet_description: '',
        has_apprentice: false,
        apprentice_name: '',
        apprentice_description: '',
        has_disciple: false,
        disciple_name: '',
        disciple_description: '',
        has_legion: false,
        legion_name: '',
        legion_description: '',
        has_legion_captain: false,
        legion_captain_name: '',
        legion_captain_description: '',
        has_behemoth: false,
        behemoth_name: '',
        behemoth_description: '',
        has_behemoth_fusion: false,
        behemoth_fusion_name: '',
        behemoth_fusion_crown: false,
        behemoth_fusion_aura: false,
        behemoth_fusion_description: '',
        visual_attributes: {
          visual_description: {
            head: body.head || '',
            torso: body.torso || '',
            arms: body.arms || '',
            legs: body.legs || '',
            aura: body.aura || '',
            ambient_flavor: body.ambient_flavor || '',
            visual_style_notes: body.visual_style_notes || '',
            color_scheme: body.color_scheme || ''
          },
          weapons: {
            weapon_1: body.weapon_1 || '',
            weapon_2: body.weapon_2 || ''
          },
          oracle_avatar_url: body.oracle_avatar_url || '',
          voice_style: body.voice_style || body.voice || '',
          role_in_pantheon: body.role_in_pantheon || body.mission || '',
          additional_notes: body.additional_notes || body.notes || ''
        }
      };
      state.oracles.unshift(oracle);
      stampActivity(state, 'oracle_created', `Created oracle profile: ${oracle.oracle_name}`);
      await saveState(state);
      return sendJson(res, 200, { ok: true, oracle });
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
