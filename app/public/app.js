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
const tabButtons = [...document.querySelectorAll('.tab-btn')];

let currentState = null;
let currentOracleId = null;
let activeTab = 'identity';

function badge(text, tone = '') {
  if (!text) return '';
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

function oracleTags(oracle) {
  return [
    badge(oracle.status, oracle.status === 'active' || oracle.status === 'seeded' ? 'good' : 'warn'),
    badge(oracle.planet),
    badge(oracle.sign),
    badge(`House ${oracle.house}`),
    badge(oracle.archetype),
    badge(oracle.productRole)
  ].filter(Boolean).join('');
}

function oracleMatchesView(oracle, view) {
  if (view === 'all') return true;
  if (view === 'council') return ['Core identity oracle', 'Emotional guidance oracle', 'Governance and structure oracle', 'Mysticism and dream logic oracle'].includes(oracle.productRole);
  if (view === 'multiplayer') return Boolean(oracle.multiplayerRole);
  if (view === 'roster') return true;
  return true;
}

function oracleMatchesSearch(oracle, query) {
  if (!query) return true;
  const haystack = [
    oracle.name,
    oracle.planet,
    oracle.sign,
    oracle.house,
    oracle.archetype,
    oracle.spiritAnimal,
    oracle.productRole,
    oracle.multiplayerRole,
    oracle.domain,
    oracle.notes
  ].join(' ').toLowerCase();
  return haystack.includes(query.toLowerCase());
}

function oracleCard(oracle) {
  return `
    <button class="item oracle-card oracle-select ${oracle.id === currentOracleId ? 'selected' : ''}" data-oracle-id="${oracle.id}">
      <h3>${oracle.name}</h3>
      <div class="badges">${oracleTags(oracle)}</div>
      <p class="meta oracle-mission">${oracle.mission}</p>
      <p class="meta"><strong>Spirit:</strong> ${oracle.spiritAnimal || '—'} • <strong>Weapon:</strong> ${oracle.weapon || '—'}</p>
      <p class="meta"><strong>Next:</strong> <span class="oracle-next">${oracle.nextAction}</span></p>
    </button>
  `;
}

function renderOracleDetail(oracle) {
  if (!oracle) {
    oracleDetailEl.innerHTML = '<p class="meta">Select or create an oracle to inspect its mission, state, and communication readiness.</p>';
    return;
  }

  const views = {
    identity: `
      <h3>${oracle.name}</h3>
      <div class="badges">
        ${badge(oracle.status, oracle.status === 'active' || oracle.status === 'seeded' ? 'good' : 'warn')}
        ${badge(oracle.planet)}
        ${badge(oracle.sign)}
        ${badge(`House ${oracle.house}`)}
        ${badge(oracle.archetype)}
      </div>
      <p class="meta"><strong>Domain:</strong> ${oracle.domain || '—'}</p>
      <p class="meta"><strong>Mission:</strong> ${oracle.mission || '—'}</p>
      <p class="meta"><strong>Spirit animal:</strong> ${oracle.spiritAnimal || '—'}</p>
      <p class="meta"><strong>Voice:</strong> ${oracle.voice || '—'}</p>
      <p class="meta"><strong>Last contact:</strong> ${oracle.lastContact ? formatDate(oracle.lastContact) : 'Not yet established'}</p>
    `,
    gameplay: `
      <h3>${oracle.name} — Gameplay</h3>
      <div class="badges">
        ${badge(oracle.productRole)}
        ${badge(oracle.multiplayerRole)}
      </div>
      <p class="meta"><strong>Weapon:</strong> ${oracle.weapon || '—'}</p>
      <p class="meta"><strong>Combat style:</strong> ${oracle.combatStyle || '—'}</p>
      <p class="meta"><strong>Multiplayer role:</strong> ${oracle.multiplayerRole || '—'}</p>
      <p class="meta"><strong>Next action:</strong> ${oracle.nextAction || '—'}</p>
    `,
    guidance: `
      <h3>${oracle.name} — Guidance</h3>
      <p class="meta"><strong>Product role:</strong> ${oracle.productRole || '—'}</p>
      <p class="meta"><strong>Guidance mission:</strong> ${oracle.mission || '—'}</p>
      <p class="meta"><strong>Suggested check-in:</strong> State your current cosmic posture, what you are amplifying, what must be avoided, and what action you recommend next.</p>
      <p class="meta"><strong>Notes:</strong> ${oracle.notes || 'None yet'}</p>
    `,
    lore: `
      <h3>${oracle.name} — Lore</h3>
      <p class="meta"><strong>Archetype:</strong> ${oracle.archetype || '—'}</p>
      <p class="meta"><strong>Spirit animal:</strong> ${oracle.spiritAnimal || '—'}</p>
      <p class="meta"><strong>Notes:</strong> ${oracle.notes || '—'}</p>
      <p class="meta"><strong>Source status:</strong> Seeded from Pantheon source material; should be refined with cleaner imports.</p>
    `
  };

  oracleDetailEl.innerHTML = views[activeTab] || views.identity;
}

function populateOracleSelect(oracles) {
  oracleSelectEl.innerHTML = oracles
    .map(oracle => `<option value="${oracle.id}">${oracle.name}</option>`)
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

  const visibleOracles = getVisibleOracles(state.oracles);
  oraclesEl.innerHTML = visibleOracles.map(oracleCard).join('');

  waitingEl.innerHTML = state.waitingOnJordon
    .map(item => card(item.title, item.detail, [badge(item.priority, item.priority === 'high' ? 'warn' : '')]))
    .join('');

  productVisionEl.innerHTML = [
    card('Elevator pitch', state.productVision.elevatorPitch, [badge('marketable product'), badge('independent voices')]),
    card('What this becomes', state.productVision.description, state.productVision.pillars.map(pillar => badge(pillar))),
    card(
      'Traction',
      `Alpha users: ${state.productVision.traction.alphaUsers} • Saturn Rising users: ${state.productVision.traction.saturnRisingUsers} • Prototype: ${state.productVision.traction.prototypeSizeKb} KB • Beta: ${state.productVision.traction.betaStatus}`,
      [badge(state.productVision.traction.backend)]
    ),
    card(
      'Market position',
      state.productVision.marketPosition.advantage,
      [badge(state.productVision.marketPosition.category)]
    ),
    card('Primary risks', state.productVision.risks.join(' • '), [badge('watchlist', 'warn')])
  ].join('');

  populateOracleSelect(state.oracles);

  const fallbackOracle = visibleOracles[0] || state.oracles[0] || null;
  const oracle = state.oracles.find(item => item.id === (selectedOracleId || currentOracleId || oracleSelectEl.value)) || fallbackOracle;
  currentOracleId = oracle?.id || null;

  if (oracle) {
    oracleSelectEl.value = oracle.id;
    renderOracleDetail(oracle);
  } else {
    renderOracleDetail(null);
  }

  document.querySelectorAll('.oracle-select').forEach(button => {
    button.addEventListener('click', () => {
      const id = button.dataset.oracleId;
      currentOracleId = id;
      oracleSelectEl.value = id;
      const selected = currentState.oracles.find(item => item.id === id);
      renderOracleDetail(selected);
      document.querySelectorAll('.oracle-select').forEach(el => el.classList.remove('selected'));
      button.classList.add('selected');
    });
  });
}

refreshBtn.addEventListener('click', () => loadState(currentOracleId));
oracleSelectEl.addEventListener('change', () => {
  currentOracleId = oracleSelectEl.value;
  const oracle = currentState?.oracles.find(item => item.id === currentOracleId);
  renderOracleDetail(oracle);
});
oracleViewFilterEl.addEventListener('change', () => loadState(currentOracleId));
oracleSearchEl.addEventListener('input', () => loadState(currentOracleId));

tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    tabButtons.forEach(button => button.classList.remove('active'));
    btn.classList.add('active');
    activeTab = btn.dataset.tab;
    const oracle = currentState?.oracles.find(item => item.id === currentOracleId);
    renderOracleDetail(oracle);
  });
});

oracleDraftBtn.addEventListener('click', () => {
  const oracleId = oracleSelectEl.value;
  const oracle = currentState?.oracles.find(item => item.id === oracleId);
  if (!oracle) return;
  const message = oracleMessageEl.value.trim() || `Report your current state, priorities, and symbolic posture regarding ${oracle.domain}.`;
  const draft = `To ${oracle.name}: ${message}`;
  addDraft(`Draft to ${oracle.name}`, draft);
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
  const oracle = currentState?.oracles?.find(item => item.id === oracleSelectEl.value) || currentState?.oracles?.[0];
  if (!oracle) return;
  addDraft(
    'Oracle check-in template',
    `State your identity, domain, current objective, unresolved tensions, and next move. Respond in a way that is faithful to your voice: ${oracle.voice}.`
  );
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
  await loadState(result.oracle?.id);
});

loadState();
setInterval(() => loadState(currentOracleId), 5000);
