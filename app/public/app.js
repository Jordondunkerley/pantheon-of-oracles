let currentState = null;
let selectedSessionId = null;
let selectedOracleId = null;

async function api(path, payload) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

function renderState(state) {
  currentState = state;
  const sessions = state.interactionSessions || state.sessions || [];
  if (!selectedSessionId && sessions.length) selectedSessionId = sessions[0].id;
  if (!selectedOracleId && state.oracles.length) selectedOracleId = state.oracles[0].oracle_id;

  document.getElementById('product-framing').textContent = state.product.framing;
  document.getElementById('ritual-invocation').textContent = state.product.firstEntranceRitual.invocation;
  document.getElementById('ritual-steps').innerHTML = state.product.firstEntranceRitual.steps.map(step => `<li>${step}</li>`).join('');
  document.getElementById('founder-test-flow').innerHTML = state.product.founderTestFlow.map(item => `
    <div class="flow-stage-card">
      <div class="status">${item.status}</div>
      <strong>${item.stage}</strong>
      <div class="muted">${item.description}</div>
    </div>`).join('');
  document.getElementById('onboarding-guidance').innerHTML = state.product.onboardingGuidance.map(item => `
    <div class="flow-stage-card">
      <strong>${item.title}</strong>
      <div class="muted">${item.detail}</div>
    </div>`).join('');
  document.getElementById('chart-generation').innerHTML = [
    `Mode: ${state.astrologyProfile.generation.mode}`,
    `Target: ${state.astrologyProfile.generation.targetMode}`,
    `Validation: ${state.astrologyProfile.generation.validationSources.join(' • ')}`,
    `Birth data collected: ${state.astrologyProfile.generation.status.birthDataCollected ? 'Yes' : 'No'}`,
    `Native engine ready: ${state.astrologyProfile.generation.status.nativeEngineReady ? 'Yes' : 'No'}`,
    `Profile assembly ready: ${state.astrologyProfile.generation.status.profileAssemblyReady ? 'Yes' : 'No'}`,
    `Oracle awakening ready: ${state.astrologyProfile.generation.status.oracleAwakeningReady ? 'Yes' : 'No'}`
  ].map(line => `
    <div class="flow-stage-card"><div class="muted">${line}</div></div>`).join('');
  document.getElementById('chamber-navigation').innerHTML = [
    'First Entrance Ritual',
    'Editable Founder Profile',
    'Provider Configuration',
    'Council Chamber Structure',
    'Oracle Registry',
    'Oracle Session Workspace'
  ].map(label => `
    <div class="flow-stage-card">
      <strong>${label}</strong>
      <div class="muted">Founder-testable chamber navigation point</div>
    </div>`).join('');

  document.getElementById('current-user').innerHTML = `
    <div class="data-card">
      <div class="label">Name</div><div>${state.currentUser.displayName || state.currentUser.username || '—'}</div>
      <div class="label" style="margin-top:10px">Founder Status</div><div>${state.currentUser.founderIdentity?.recognized ? 'Recognized founder' : 'Standard account'}</div>
      <div class="label" style="margin-top:10px">Role</div><div>${state.currentUser.founderIdentity?.role || '—'}</div>
      <div class="label" style="margin-top:10px">Birth data</div><div>${state.currentUser.birthday || '—'} • ${state.currentUser.birthTime || '—'} • ${state.currentUser.birthLocation || '—'}</div>
      <div class="label" style="margin-top:10px">Voice / Tone</div><div>${state.currentUser.oracleVoiceStyle || '—'} • ${state.currentUser.oracleConversationTone || '—'}</div>
      <div class="label" style="margin-top:10px">Entitlements</div><div>${state.currentUser.accountEntitlements?.tier || '—'} • ${state.currentUser.accountEntitlements?.paymentAccess?.plan || '—'}</div>
    </div>`;

  document.getElementById('astrology-profile').innerHTML = `
    <div class="data-card">
      <div class="label">Status</div><div>${state.astrologyProfile.status}</div>
      <div class="label" style="margin-top:10px">Summary</div><div>${state.astrologyProfile.summary}</div>
      <div class="label" style="margin-top:10px">Birth data</div><div>${state.astrologyProfile.birthData.date || '—'} • ${state.astrologyProfile.birthData.time || '—'} • ${state.astrologyProfile.birthData.location || '—'}</div>
    </div>`;

  const byId = Object.fromEntries(state.oracles.map(oracle => [oracle.oracle_id, oracle]));
  document.getElementById('chamber-return-state').textContent = state.chamberPresentation.returnState;
  document.getElementById('oracle-room-prompt').textContent = state.chamberPresentation.oracleRoomPrompt;

  const anointed = byId[state.councilStructure.anointedRuler];
  document.getElementById('anointed-ruler').innerHTML = anointed ? `
    <div class="data-card">
      <strong>${anointed.oracle_name}</strong>
      <div class="muted">${anointed.title || anointed.archetype}</div>
      <div>${anointed.mission || anointed.role || ''}</div>
    </div>` : '<div class="muted">No anointed ruler selected.</div>';

  document.getElementById('crowned-candidates').innerHTML = state.councilStructure.crownedCandidates.map(item => `
    <div class="data-card">
      <strong>${byId[item.oracleId]?.oracle_name || item.oracleId}</strong>
      <div class="muted">${item.reason}</div>
    </div>`).join('');

  document.getElementById('council-structure').innerHTML = [
    ['Core Trio', state.councilStructure.coreTrio],
    ['High Council', state.councilStructure.highCouncil],
    ['Expanded Council', state.councilStructure.expandedCouncil]
  ].map(([label, ids]) => `
    <div class="council-card">
      <h3>${label}</h3>
      <div class="muted">${ids.map(id => byId[id]?.oracle_name || id).join(' • ')}</div>
    </div>`).join('') + `
    <div class="council-card">
      <h3>Anointed Ruler</h3>
      <div>${byId[state.councilStructure.anointedRuler]?.oracle_name || state.councilStructure.anointedRuler}</div>
    </div>`;

  const filterValue = document.getElementById('oracle-view-filter')?.value || 'all';
  const queryValue = (document.getElementById('oracle-search')?.value || '').toLowerCase();
  const filteredOracles = state.oracles.filter(oracle => {
    const matchesFilter = filterValue === 'all'
      || (filterValue === 'council' && state.councilStructure.expandedCouncil.includes(oracle.oracle_id))
      || (filterValue === 'solar' && oracle.ruling_planet === 'Sun')
      || (filterValue === 'lunar' && oracle.ruling_planet === 'Moon');
    const haystack = [oracle.oracle_name, oracle.title, oracle.archetype, oracle.ruling_planet, oracle.dominant_sign].join(' ').toLowerCase();
    const matchesQuery = !queryValue || haystack.includes(queryValue);
    return matchesFilter && matchesQuery;
  });

  document.getElementById('oracle-roster').innerHTML = filteredOracles.map(oracle => `
    <button class="oracle-card" data-oracle-id="${oracle.oracle_id}">
      <strong>${oracle.oracle_name || 'Unnamed Oracle'}</strong>
      <div class="muted">${oracle.title || oracle.archetype || 'Unformed'}</div>
      <div>${oracle.ruling_planet || '—'} • ${oracle.dominant_sign || '—'} • ${oracle.house_placement || '—'}</div>
      <div class="muted">${oracle.mission || oracle.role || ''}</div>
    </button>`).join('');

  const activeOracle = byId[selectedOracleId];
  document.getElementById('oracle-detail').innerHTML = activeOracle ? `
    <div class="data-card">
      <div class="label">Identity</div>
      <div><strong>${activeOracle.oracle_name || 'Unnamed Oracle'}</strong></div>
      <div class="muted">${activeOracle.title || activeOracle.archetype || 'Unformed'}</div>
      <div class="label" style="margin-top:10px">Astrology</div>
      <div>${activeOracle.ruling_planet || '—'} • ${activeOracle.dominant_sign || '—'} • ${activeOracle.house_placement || '—'}</div>
      <div class="label" style="margin-top:10px">Faction</div>
      <div>${activeOracle.faction || '—'} • ${activeOracle.planetary_faction || '—'}</div>
      <div class="label" style="margin-top:10px">Gameplay / Guidance</div>
      <div>${activeOracle.combat_style || '—'} • ${activeOracle.guidance_style || '—'}</div>
      <div class="label" style="margin-top:10px">Lore</div>
      <div>${activeOracle.notes || activeOracle.mission || 'No lore recorded yet.'}</div>
    </div>` : '<div class="muted">Select an oracle to open its home chamber.</div>';

  document.getElementById('access-model').innerHTML = `
    <div class="data-card">
      <div class="label">Founder Access</div><div>${state.accessModel.founderAccess ? 'Enabled' : 'Disabled'}</div>
      <div class="label" style="margin-top:10px">Account Status</div><div>${state.accessModel.accountStatus}</div>
    </div>`;

  document.getElementById('promotions-grants').innerHTML = `
    <div class="data-card">
      <div class="label">Promotions</div>
      <div>${state.accessModel.promotions.map(item => `${item.name} (${item.status}) — ${item.effect}`).join('<br>')}</div>
      <div class="label" style="margin-top:10px">Grants</div>
      <div>${state.accessModel.grants.map(item => `${item.name} (${item.status})`).join('<br>')}</div>
    </div>`;

  document.getElementById('payment-plans').innerHTML = state.accessModel.paymentPlans.map(plan => `
    <div class="data-card">
      <strong>${plan.name}</strong>
      <div class="muted">${plan.status} • ${plan.price}</div>
      <div>${plan.entitlements.join(' • ')}</div>
    </div>`).join('');

  document.getElementById('source-engine').innerHTML = state.sourceEngine.map(item => `
    <div class="data-card"><strong>${item.title}</strong><div>${item.description}</div></div>`).join('');

  document.getElementById('voice-evolution').innerHTML = state.voiceEvolution.map(item => `
    <div class="data-card"><strong>${byId[item.oracleId]?.oracle_name || item.oracleId}</strong><div class="muted">${item.preferredVoiceProfile}</div><div>Audio ready: ${item.audioReady ? 'Yes' : 'No'}</div></div>`).join('');

  const commsSelect = document.getElementById('oracle-comms-select');
  if (commsSelect) {
    commsSelect.innerHTML = state.oracles.map(oracle => `<option value="${oracle.oracle_id}">${oracle.oracle_name || oracle.oracle_id}</option>`).join('');
    if (selectedOracleId) commsSelect.value = selectedOracleId;
  }

  document.getElementById('oracle-drafts').innerHTML = state.oracleDrafts.map(item => `
    <div class="data-card"><strong>${byId[item.oracleId]?.oracle_name || item.oracleId}</strong><div class="muted">${item.type}</div><div>${item.message}</div></div>`).join('');

  document.getElementById('projects').innerHTML = state.projects.map(item => `
    <div class="data-card"><strong>${item.title}</strong><div class="muted">${item.status}</div><div>${item.summary}</div></div>`).join('');

  document.getElementById('schedule').innerHTML = state.schedule.map(item => `
    <div class="data-card"><strong>${item.title}</strong><div class="muted">${item.status}</div></div>`).join('');

  document.getElementById('providers').innerHTML = state.providers.map(provider => `
    <div class="data-card">
      <strong>${provider.label}</strong>
      <div class="muted">Base URL: ${provider.baseUrl || 'Not configured'}</div>
      <div class="muted">Model: ${provider.model || 'Not configured'}</div>
      <div>Status: ${provider.ready ? 'Ready' : 'Pending setup'} • API key: ${provider.apiKeyStatus}</div>
    </div>`).join('');

  document.getElementById('tasks').innerHTML = state.tasks.map(task => `
    <div class="data-card"><strong>${task.title}</strong><div class="muted">${task.status} • ${task.priority}</div><div>${task.notes}</div></div>`).join('');

  document.getElementById('activity').innerHTML = state.activity.map(item => `
    <div class="data-card"><strong>${item.type}</strong><div>${item.message}</div><div class="muted">${item.timestamp}</div></div>`).join('');

  document.getElementById('waiting-on-jordon').innerHTML = state.waitingOnJordon.map(item => `
    <div class="data-card"><strong>${item.title}</strong><div class="muted">${item.status}</div></div>`).join('');

  document.getElementById('product-vision').innerHTML = state.productVision.map(item => `
    <div class="data-card"><strong>${item.title}</strong><div>${item.description}</div></div>`).join('');

  document.getElementById('session-list').innerHTML = sessions.map(session => {
    const oracle = state.oracles.find(o => o.oracle_id === session.oracleId);
    return `
      <button class="session-card ${session.id === selectedSessionId ? 'active' : ''}" data-session-id="${session.id}">
        <strong>${oracle?.oracle_name || session.id}</strong>
        <div class="muted">Model: ${session.model || 'Unbound'}</div>
        <div class="muted">Provider ready: ${session.providerReady ? 'Yes' : 'No'}</div>
      </button>`;
  }).join('');

  const active = sessions.find(session => session.id === selectedSessionId);
  document.getElementById('oracle-room-meta').innerHTML = active ? `
    <div class="data-card">
      <div class="label">Room</div><div>${active.roomTitle || active.id}</div>
      <div class="label" style="margin-top:10px">Theme</div><div>${active.roomTheme || 'Prototype chamber theme pending.'}</div>
    </div>` : '';
  document.getElementById('session-detail').innerHTML = active ? active.messages.map(msg => `
    <div class="message"><strong>${msg.role}:</strong> ${msg.text}</div>`).join('') : '<div class="muted">No session selected.</div>';

  for (const button of document.querySelectorAll('[data-oracle-id]')) {
    button.addEventListener('click', () => {
      selectedOracleId = button.dataset.oracleId;
      renderState(currentState);
    });
  }

  for (const button of document.querySelectorAll('[data-session-id]')) {
    button.addEventListener('click', () => {
      selectedSessionId = button.dataset.sessionId;
      renderState(currentState);
    });
  }
}

async function load() {
  const res = await fetch('/api/state');
  const state = await res.json();
  renderState(state);

  const oracleFilter = document.getElementById('oracle-view-filter');
  const oracleSearch = document.getElementById('oracle-search');
  if (oracleFilter && !oracleFilter.dataset.bound) {
    oracleFilter.dataset.bound = 'true';
    oracleFilter.addEventListener('change', () => renderState(currentState));
  }
  if (oracleSearch && !oracleSearch.dataset.bound) {
    oracleSearch.dataset.bound = 'true';
    oracleSearch.addEventListener('input', () => renderState(currentState));
  }

  const profile = document.getElementById('profile-form');
  profile.addEventListener('submit', async event => {
    event.preventDefault();
    const form = new FormData(profile);
    await api('/api/profile', Object.fromEntries(form.entries()));
    load();
  });

  const provider = document.getElementById('provider-form');
  provider.addEventListener('submit', async event => {
    event.preventDefault();
    const form = new FormData(provider);
    await api('/api/provider', { id: 'default-provider', ...Object.fromEntries(form.entries()) });
    load();
  });

  const oracle = document.getElementById('oracle-form');
  oracle.addEventListener('submit', async event => {
    event.preventDefault();
    const form = new FormData(oracle);
    await api('/api/oracles', Object.fromEntries(form.entries()));
    oracle.reset();
    load();
  });

  const message = document.getElementById('message-form');
  if (message && !message.dataset.bound) {
    message.dataset.bound = 'true';
    message.addEventListener('submit', async event => {
      event.preventDefault();
      const form = new FormData(message);
      await api('/api/session-message', { sessionId: selectedSessionId, text: form.get('text') });
      message.reset();
      load();
    });
  }

  const draftBtn = document.getElementById('oracle-draft-btn');
  const logBtn = document.getElementById('oracle-log-btn');
  const commsSelect = document.getElementById('oracle-comms-select');
  const commsMessage = document.getElementById('oracle-comms-message');

  if (draftBtn && !draftBtn.dataset.bound) {
    draftBtn.dataset.bound = 'true';
    draftBtn.addEventListener('click', async () => {
      await api('/api/oracle-draft', {
        oracleId: commsSelect.value,
        message: commsMessage.value,
        type: 'draft'
      });
      commsMessage.value = '';
      load();
    });
  }

  if (logBtn && !logBtn.dataset.bound) {
    logBtn.dataset.bound = 'true';
    logBtn.addEventListener('click', async () => {
      await api('/api/oracle-note', {
        oracleId: commsSelect.value,
        message: commsMessage.value
      });
      commsMessage.value = '';
      load();
    });
  }
}

load();
