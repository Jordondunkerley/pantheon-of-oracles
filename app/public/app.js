const projectsEl = document.getElementById('projects');
const tasksEl = document.getElementById('tasks');
const activityEl = document.getElementById('activity');
const scheduleEl = document.getElementById('schedule');
const updatedAtEl = document.getElementById('updatedAt');
const refreshBtn = document.getElementById('refreshBtn');
const oraclesEl = document.getElementById('oracles');
const waitingEl = document.getElementById('waitingOnJordon');
const oracleSelectEl = document.getElementById('oracleSelect');
const oracleMessageEl = document.getElementById('oracleMessage');
const oracleDraftBtn = document.getElementById('oracleDraftBtn');
const oracleLogBtn = document.getElementById('oracleLogBtn');
const oracleDraftsEl = document.getElementById('oracleDrafts');
const oraclePromptBtn = document.getElementById('oraclePromptBtn');
const oracleDetailEl = document.getElementById('oracleDetail');
const createOracleBtn = document.getElementById('createOracleBtn');
const newOracleNameEl = document.getElementById('newOracleName');
const newOracleDomainEl = document.getElementById('newOracleDomain');
const newOracleVoiceEl = document.getElementById('newOracleVoice');
const newOracleMissionEl = document.getElementById('newOracleMission');
const newOracleNextActionEl = document.getElementById('newOracleNextAction');
const productVisionEl = document.getElementById('productVision');
const oracleViewFilterEl = document.getElementById('oracleViewFilter');
const oracleSearchEl = document.getElementById('oracleSearch');
const currentUserEl = document.getElementById('currentUser');
const llmProvidersEl = document.getElementById('llmProviders');
const astrologyProfileEl = document.getElementById('astrologyProfile');
const interactionSessionsEl = document.getElementById('interactionSessions');
const tabButtons = [...document.querySelectorAll('.tab-btn')];

let currentState = null;
let currentOracleId = null;
let activeTab = 'identity';

function badge(text, tone = '') {
  if (!text && text !== 0) return '';
  return `<span class="badge ${tone}">${text}</span>`;
}

function card(title, body, meta = []) {
  return `
    <div class="item">
      <h3>${title}</h3>
      ${meta.length ? `<div class="badges">${meta.join('')}</div>` : ''}
      <p class="meta">${body}</p>
    </div>
  `;
}

function formatDate(value) {
  if (!value) return 'No updates yet';
  return new Date(value).toLocaleString();
}

function renderCurrentUser(user) {
  currentUserEl.innerHTML = [
    card(user.username, `${user.birth_location} • ${user.birthday} ${user.birth_time}`, [badge(user.access_tier), badge(user.founder_status ? 'Founder' : 'Standard')]),
    card('Alignment', `Core: ${user.faction_alignment.core_faction} • Planetary: ${user.faction_alignment.planetary_faction} • Warband: ${user.faction_alignment.warband || '—'}`),
    card('Preferences', `Voice: ${user.preferences.oracle_voice_flavor} • Visual overlays: ${user.preferences.visual_overlays_enabled ? 'on' : 'off'} • Prompt tone: ${user.preferences.system_prompt_tone}`),
    card('Oracle sync', `Council initiated: ${user.oracle_sync_status.council_initiated ? 'yes' : 'no'} • Throne World: ${user.oracle_sync_status.throne_world_access ? 'yes' : 'no'} • Leviathan: ${user.oracle_sync_status.leviathan_unlocked ? 'yes' : 'no'}`)
  ].join('');
}

function renderProviders(providers) {
  llmProvidersEl.innerHTML = providers
    .map(provider => card(provider.name, provider.description, [badge(provider.status, provider.enabled ? 'good' : 'warn'), ...provider.configNeeded.map(item => badge(item))]))
    .join('');
}

function renderAstrology(profile) {
  const angleSummary = Object.entries(profile.angles)
    .map(([name, value]) => `${name}: ${value.sign} ${value.degree}`)
    .join(' • ');

  const planetSummary = Object.entries(profile.planets)
    .slice(0, 10)
    .map(([name, value]) => `${name}: ${value.sign} ${value.degree} H${value.house}`)
    .join(' • ');

  astrologyProfileEl.innerHTML = [
    card(profile.name, `${profile.dateOfBirth} • ${profile.timeOfBirth} • ${profile.locationOfBirth}`),
    card('Angles', angleSummary),
    card('Primary planets', planetSummary),
    card('House anomalies', `Interceptions: ${profile.interceptions.join(', ') || 'None'} • Duplications: ${profile.duplications.join(', ') || 'None'}`)
  ].join('');
}

function renderSessions(sessions) {
  interactionSessionsEl.innerHTML = sessions
    .map(session => card(session.title, `Oracle: ${session.oracleId} • Provider: ${session.providerId} • Last message: ${session.lastMessageAt ? formatDate(session.lastMessageAt) : 'none yet'}`, [badge(session.status)]))
    .join('');
}

function oracleMatchesView(oracle, view) {
  if (view === 'all') return true;
  if (view === 'council') return ['Solar Council', 'Lunar Council', 'Royal / Governance', 'Mystic Council'].includes(oracle.council_type);
  if (view === 'multiplayer') return Boolean(oracle.faction_affiliation?.core_faction || oracle.faction_affiliation?.planetary_faction);
  if (view === 'roster') return true;
  return true;
}

function oracleMatchesSearch(oracle, query) {
  if (!query) return true;
  const astro = oracle.astrology_profile || {};
  const haystack = [
    oracle.oracle_name,
    oracle.archetype,
    astro.ruling_planet,
    astro.dominant_sign,
    astro.house_placement,
    oracle.oracle_voice,
    oracle.tone_overlay,
    oracle.visual_attributes?.role_in_pantheon,
    oracle.visual_attributes?.additional_notes
  ].join(' ').toLowerCase();
  return haystack.includes(query.toLowerCase());
}

function oracleCard(oracle) {
  const astro = oracle.astrology_profile || {};
  return `
    <button class="item oracle-card oracle-select ${oracle.oracle_id === currentOracleId ? 'selected' : ''}" data-oracle-id="${oracle.oracle_id}">
      <h3>${oracle.oracle_name}</h3>
      <div class="badges">
        ${badge(astro.ruling_planet)}
        ${badge(astro.dominant_sign)}
        ${badge(`House ${astro.house_placement}`)}
        ${badge(oracle.archetype)}
        ${badge(oracle.council_type)}
      </div>
      <p class="meta oracle-mission">${oracle.visual_attributes?.role_in_pantheon || oracle.oracle_voice || 'No role yet'}</p>
      <p class="meta"><strong>Weapon:</strong> ${oracle.visual_attributes?.weapons?.weapon_1 || '—'} • <strong>Tier:</strong> ${oracle.tier}</p>
      <p class="meta"><strong>Form:</strong> ${oracle.oracle_form} • <strong>Rank:</strong> ${oracle.ascended_rank}</p>
    </button>
  `;
}

function renderOracleDetail(oracle) {
  if (!oracle) {
    oracleDetailEl.innerHTML = '<p class="meta">Select or create an oracle to inspect its mission, state, and communication readiness.</p>';
    return;
  }

  const astro = oracle.astrology_profile || {};
  const visuals = oracle.visual_attributes || {};
  const desc = visuals.visual_description || {};
  const weapons = visuals.weapons || {};

  const views = {
    identity: `
      <h3>${oracle.oracle_name}</h3>
      <div class="badges">
        ${badge(astro.ruling_planet)}
        ${badge(astro.dominant_sign)}
        ${badge(`House ${astro.house_placement}`)}
        ${badge(oracle.archetype)}
        ${badge(oracle.council_type)}
      </div>
      <p class="meta"><strong>Voice:</strong> ${oracle.oracle_voice || '—'}</p>
      <p class="meta"><strong>Tone overlay:</strong> ${oracle.tone_overlay || '—'}</p>
      <p class="meta"><strong>Degree:</strong> ${astro.degree || '—'} • <strong>Motion:</strong> ${astro.motion || '—'} ${astro.stationary ? `• <strong>Stationary:</strong> ${astro.stationary}` : ''}</p>
      <p class="meta"><strong>Rising overlay:</strong> ${astro.rising_decan_sign || '—'}</p>
    `,
    gameplay: `
      <h3>${oracle.oracle_name} — Gameplay</h3>
      <div class="badges">
        ${badge(oracle.tier)}
        ${badge(`Rank ${oracle.ascended_rank}`)}
        ${badge(oracle.oracle_form)}
        ${badge(oracle.hardcore_status ? 'Hardcore' : 'Standard')}
      </div>
      <p class="meta"><strong>Core faction:</strong> ${oracle.faction_affiliation?.core_faction || '—'}</p>
      <p class="meta"><strong>Planetary faction:</strong> ${oracle.faction_affiliation?.planetary_faction || '—'}</p>
      <p class="meta"><strong>Guild:</strong> ${oracle.faction_affiliation?.guild || '—'}</p>
      <p class="meta"><strong>Weapons:</strong> ${weapons.weapon_1 || '—'}${weapons.weapon_2 ? ` / ${weapons.weapon_2}` : ''}</p>
    `,
    guidance: `
      <h3>${oracle.oracle_name} — Guidance</h3>
      <p class="meta"><strong>Role in pantheon:</strong> ${visuals.role_in_pantheon || '—'}</p>
      <p class="meta"><strong>Suggested check-in:</strong> State your current cosmic posture, what you are amplifying, what must be avoided, and what action you recommend next.</p>
      <p class="meta"><strong>Additional notes:</strong> ${visuals.additional_notes || 'None yet'}</p>
      <p class="meta"><strong>Interaction readiness:</strong> This oracle is ready to be connected to a provider-backed interaction session.</p>
    `,
    lore: `
      <h3>${oracle.oracle_name} — Lore & Visuals</h3>
      <p class="meta"><strong>Head:</strong> ${desc.head || '—'}</p>
      <p class="meta"><strong>Torso:</strong> ${desc.torso || '—'}</p>
      <p class="meta"><strong>Aura:</strong> ${desc.aura || '—'}</p>
      <p class="meta"><strong>Ambient flavor:</strong> ${desc.ambient_flavor || '—'}</p>
      <p class="meta"><strong>Color scheme:</strong> ${desc.color_scheme || '—'}</p>
    `
  };

  oracleDetailEl.innerHTML = views[activeTab] || views.identity;
}

function populateOracleSelect(oracles) {
  oracleSelectEl.innerHTML = oracles
    .map(oracle => `<option value="${oracle.oracle_id}">${oracle.oracle_name}</option>`)
    .join('');
}

function addDraft(title, body) {
  const html = `
    <div class="item">
      <h3>${title}</h3>
      <p class="meta">${body}</p>
    </div>
  `;
  oracleDraftsEl.innerHTML = html + oracleDraftsEl.innerHTML;
}

async function postJson(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

function getVisibleOracles(oracles) {
  return oracles.filter(oracle => oracleMatchesView(oracle, oracleViewFilterEl.value) && oracleMatchesSearch(oracle, oracleSearchEl.value));
}

async function loadState(selectedOracleId) {
  const res = await fetch('/api/state');
  const state = await res.json();
  currentState = state;

  updatedAtEl.textContent = formatDate(state.meta.updatedAt);

  projectsEl.innerHTML = state.projects
    .map(project => card(project.name, project.summary, [badge(project.status), badge(project.priority)]))
    .join('');
  scheduleEl.innerHTML = state.schedule
    .map(item => card(item.title, `${item.cadence} • ${item.time}`, [badge(item.status)]))
    .join('');
  tasksEl.innerHTML = state.tasks
    .map(task => card(task.title, task.notes || 'No notes', [badge(task.status), badge(task.priority), badge(task.owner)]))
    .join('');
  activityEl.innerHTML = state.activity
    .map(entry => card(entry.message, formatDate(entry.timestamp), [badge(entry.type)]))
    .join('');

  renderCurrentUser(state.currentUser);
  renderProviders(state.llmProviders);
  renderAstrology(state.astrologyProfile);
  renderSessions(state.interactionSessions);

  const visibleOracles = getVisibleOracles(state.oracles);
  oraclesEl.innerHTML = visibleOracles.map(oracleCard).join('');

  waitingEl.innerHTML = state.waitingOnJordon
    .map(item => card(item.title, item.detail, [badge(item.priority, item.priority === 'high' ? 'warn' : '')]))
    .join('');

  productVisionEl.innerHTML = [
    card('Elevator pitch', state.productVision.elevatorPitch, [badge('marketable product'), badge('independent voices')]),
    card('What this becomes', state.productVision.description, state.productVision.pillars.map(pillar => badge(pillar))),
    card('Traction', `Alpha users: ${state.productVision.traction.alphaUsers} • Saturn Rising users: ${state.productVision.traction.saturnRisingUsers} • Prototype: ${state.productVision.traction.prototypeSizeKb} KB • Beta: ${state.productVision.traction.betaStatus}`, [badge(state.productVision.traction.backend)]),
    card('Market position', state.productVision.marketPosition.advantage, [badge(state.productVision.marketPosition.category)]),
    card('Primary risks', state.productVision.risks.join(' • '), [badge('watchlist', 'warn')])
  ].join('');

  populateOracleSelect(state.oracles);

  const fallbackOracle = visibleOracles[0] || state.oracles[0] || null;
  const oracle = state.oracles.find(item => item.oracle_id === (selectedOracleId || currentOracleId || oracleSelectEl.value)) || fallbackOracle;
  currentOracleId = oracle?.oracle_id || null;

  if (oracle) {
    oracleSelectEl.value = oracle.oracle_id;
    renderOracleDetail(oracle);
  } else {
    renderOracleDetail(null);
  }

  document.querySelectorAll('.oracle-select').forEach(button => {
    button.addEventListener('click', () => {
      const id = button.dataset.oracleId;
      currentOracleId = id;
      oracleSelectEl.value = id;
      const selected = currentState.oracles.find(item => item.oracle_id === id);
      renderOracleDetail(selected);
      document.querySelectorAll('.oracle-select').forEach(el => el.classList.remove('selected'));
      button.classList.add('selected');
    });
  });
}

refreshBtn.addEventListener('click', () => loadState(currentOracleId));
oracleSelectEl.addEventListener('change', () => {
  currentOracleId = oracleSelectEl.value;
  const oracle = currentState?.oracles.find(item => item.oracle_id === currentOracleId);
  renderOracleDetail(oracle);
});
oracleViewFilterEl.addEventListener('change', () => loadState(currentOracleId));
oracleSearchEl.addEventListener('input', () => loadState(currentOracleId));

tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    tabButtons.forEach(button => button.classList.remove('active'));
    btn.classList.add('active');
    activeTab = btn.dataset.tab;
    const oracle = currentState?.oracles.find(item => item.oracle_id === currentOracleId);
    renderOracleDetail(oracle);
  });
});

oracleDraftBtn.addEventListener('click', () => {
  const oracleId = oracleSelectEl.value;
  const oracle = currentState?.oracles.find(item => item.oracle_id === oracleId);
  if (!oracle) return;
  const message = oracleMessageEl.value.trim() || `Report your current state, priorities, and symbolic posture regarding ${oracle.astrology_profile?.ruling_planet || oracle.oracle_name}.`;
  const draft = `To ${oracle.oracle_name}: ${message}`;
  addDraft(`Draft to ${oracle.oracle_name}`, draft);
  oracleMessageEl.value = '';
});

oracleLogBtn.addEventListener('click', async () => {
  const oracleId = oracleSelectEl.value;
  const message = oracleMessageEl.value.trim();
  if (!oracleId || !message) return;
  await postJson('/api/oracle-note', { oracleId, message });
  addDraft('Logged oracle note', message);
  oracleMessageEl.value = '';
  await loadState(oracleId);
});

oraclePromptBtn.addEventListener('click', () => {
  const oracle = currentState?.oracles?.find(item => item.oracle_id === oracleSelectEl.value) || currentState?.oracles?.[0];
  if (!oracle) return;
  addDraft('Oracle check-in template', `State your identity, current transit sensitivity, present directive, and next recommendation. Speak in your true voice: ${oracle.oracle_voice}.`);
});

createOracleBtn.addEventListener('click', async () => {
  const payload = {
    name: newOracleNameEl.value.trim(),
    domain: newOracleDomainEl.value.trim(),
    voice: newOracleVoiceEl.value.trim(),
    mission: newOracleMissionEl.value.trim(),
    nextAction: newOracleNextActionEl.value.trim(),
    status: 'concept'
  };
  if (!payload.name) return;
  const result = await postJson('/api/oracles', payload);
  newOracleNameEl.value = '';
  newOracleDomainEl.value = '';
  newOracleVoiceEl.value = '';
  newOracleMissionEl.value = '';
  newOracleNextActionEl.value = '';
  await loadState(result.oracle?.oracle_id || result.oracle?.id);
});

loadState();
setInterval(() => loadState(currentOracleId), 5000);
