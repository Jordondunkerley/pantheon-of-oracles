let currentState = null;
let selectedSessionId = null;
let selectedOracleId = null;
let selectedRulerPath = null;
let currentScene = 'title-screen';
let chamberAnnouncement = '';

async function api(path, payload) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

function sceneLabel(scene) {
  return scene.replace(/-/g, ' ');
}

function sceneCta(scene) {
  const map = {
    'title-screen': 'Cross the Threshold',
    'first-entrance': 'Begin the First Entrance Rite',
    'chart-awakening': 'Awaken the Birth Chart',
    'council-formation': 'Call the Council to Form',
    'chamber-hub': 'Return to the Chamber Hub',
    'oracle-room': 'Step into the Oracle Room'
  };
  return map[scene] || sceneLabel(scene);
}

function sceneFlavor(scene) {
  const map = {
    'title-screen': 'The threshold hums before the first deliberate step.',
    'first-entrance': 'The chamber listens as the founder names themself to the rite.',
    'chart-awakening': 'The sky is translated into structure, omen, and council logic.',
    'council-formation': 'Presences gather closer to the throne of guidance.',
    'chamber-hub': 'The chamber settles into a navigable living center.',
    'oracle-room': 'A single oracle steps forward and the room narrows around their presence.'
  };
  return map[scene] || '';
}

function isUnlocked(state, sceneId) {
  return state.progressionState.unlockedScenes.includes(sceneId);
}

function pulseScene(sceneId) {
  const element = document.getElementById(`scene-${sceneId}`);
  if (!element) return;
  element.classList.remove('scene-entering');
  void element.offsetWidth;
  element.classList.add('scene-entering');

  const echo = document.querySelector('.chamber-echo-line');
  if (echo) {
    echo.classList.remove('echo-pulse');
    void echo.offsetWidth;
    echo.classList.add('echo-pulse');
  }
}

function summonTone(orderIndex) {
  if (orderIndex === 0) return 'The chamber crown descends first.';
  if (orderIndex === 1) return 'The solar flame answers second.';
  if (orderIndex === 2) return 'The lunar tide arrives third.';
  return 'A distant presence lingers beyond the inner circle.';
}

function summonStateLabel(orderIndex) {
  if (orderIndex === 0) return 'First Summoned';
  if (orderIndex === 1) return 'Second Summoned';
  if (orderIndex === 2) return 'Third Summoned';
  return 'Outer Presence';
}

function progressionPayoff(state) {
  const completed = state.progressionState.completedScenes.length;
  const unlocked = state.progressionState.unlockedScenes.length;
  return `Scenes crossed: ${completed}. Chambers opened: ${unlocked}. Next rite: ${sceneCta(state.progressionState.nextRecommendedScene)}.`;
}

function activeSceneState(sceneId) {
  return `${sceneCta(sceneId)} is active. ${sceneFlavor(sceneId)}`;
}

function chamberConsequence(state) {
  const completed = state.progressionState.completedScenes.length;
  if (completed <= 1) return 'The chamber is only beginning to remember you.';
  if (completed <= 3) return 'The chamber has started to reshape itself around your passage.';
  return 'The chamber now bears the marks of repeated rites and answered thresholds.';
}

function setScene(sceneId) {
  if (!currentState || !isUnlocked(currentState, sceneId)) return;
  currentScene = sceneId;
  chamberAnnouncement = `${sceneCta(sceneId)} rises into focus. The chamber shifts around you.`;
  currentState.progressionState.currentScene = sceneId;
  for (const scene of document.querySelectorAll('.scene')) {
    scene.classList.toggle('hidden-scene', scene.id !== `scene-${sceneId}`);
    scene.classList.toggle('active-scene', scene.id === `scene-${sceneId}`);
  }
  for (const button of document.querySelectorAll('[data-scene-id]')) {
    button.classList.toggle('selected', button.dataset.sceneId === sceneId);
    button.disabled = !isUnlocked(currentState, button.dataset.sceneId);
  }
  pulseScene(sceneId);
}

function unlockScene(state, sceneId) {
  if (!state.progressionState.unlockedScenes.includes(sceneId)) {
    state.progressionState.unlockedScenes.push(sceneId);
    chamberAnnouncement = `${sceneCta(sceneId)} is now unlocked. The chamber answers your progress.`;
    const payoff = document.getElementById('progression-payoff');
    if (payoff) {
      payoff.classList.remove('payoff-pulse');
      void payoff.offsetWidth;
      payoff.classList.add('payoff-pulse');
    }
  }
}

function renderState(state) {
  currentState = state;
  const sessions = state.interactionSessions || state.sessions || [];
  if (!selectedSessionId && sessions.length) selectedSessionId = sessions[0].id;
  if (!selectedOracleId && state.oracles.length) selectedOracleId = state.oracles[0].oracle_id;

  document.getElementById('product-framing').textContent = state.product.framing;
  const announcementEl = document.getElementById('chamber-announcement');
  if (announcementEl) {
    announcementEl.textContent = chamberAnnouncement || 'The chamber stands ready for the next rite.';
    announcementEl.classList.remove('announcement-active');
    void announcementEl.offsetWidth;
    announcementEl.classList.add('announcement-active');
  }
  const shell = document.querySelector('.game-shell');
  if (shell) {
    shell.dataset.scene = currentScene;
  }
  document.getElementById('scene-pills').innerHTML = state.product.sceneFlow.map(scene => {
    const unlocked = isUnlocked(state, scene);
    return `<button data-scene-id="${scene}" ${unlocked ? '' : 'disabled'}>${sceneCta(scene)}${unlocked ? '' : ' 🔒'}<span class="scene-flavor">${sceneFlavor(scene)}</span></button>`;
  }).join('');

  document.getElementById('progression-payoff').innerHTML = `<div class="label">Progression Payoff</div><strong>${progressionPayoff(state)}</strong><div class="scene-flavor">The chamber should make advancement feel earned, counted, and real.</div>`;
  document.getElementById('active-scene-state').innerHTML = `<div class="label">Active Scene</div><strong>${activeSceneState(currentScene)}</strong><div class="scene-flavor">${chamberConsequence(state)}</div>`;
  document.getElementById('milestones').innerHTML = state.progressionState.milestones.map(item => `
    <div class="data-card reveal-card ${item.status}"><strong>${item.title}</strong><div class="muted">${item.description}</div><div class="label">${item.status}</div></div>`).join('');
  document.getElementById('reward-moments').innerHTML = state.progressionState.rewardMoments.map(item => `
    <div class="data-card reward-card reveal-card ${item.state}"><strong>${item.title}</strong><div class="muted">${item.description}</div><div class="label">${item.state}</div></div>`).join('');

  document.getElementById('title-screen-content').innerHTML = [
    { title: 'Recovered Chamber', body: 'The chamber has been reclaimed and now awaits a more ceremonial flow.' },
    { title: 'Current Pulse', body: 'Scene-based progression, rite language, and reveal-driven UX are actively forming.' },
    { title: 'Next Rite', body: sceneCta(state.progressionState.nextRecommendedScene) },
    { title: 'Threshold Feeling', body: sceneFlavor(currentScene) }
  ].map(item => `<div class="data-card reveal-card threshold-card"><strong>${item.title}</strong><div class="muted">${item.body}</div></div>`).join('');

  document.getElementById('ritual-invocation').textContent = state.product.firstEntranceRitual.invocation;
  document.getElementById('ritual-steps').innerHTML = state.product.firstEntranceRitual.steps.map(step => `<li>${step}</li>`).join('');

  document.getElementById('chart-generation').innerHTML = [
    `Mode: ${state.astrologyProfile.generation.mode}`,
    `Target: ${state.astrologyProfile.generation.targetMode}`,
    `Validation: ${state.astrologyProfile.generation.validationSources.join(' • ')}`,
    `Birth data gathered: ${state.astrologyProfile.generation.status.birthDataCollected ? 'Yes' : 'No'}`,
    `Native engine awakened: ${state.astrologyProfile.generation.status.nativeEngineReady ? 'Yes' : 'No'}`,
    `Council awakening path: ${state.astrologyProfile.generation.status.oracleAwakeningReady ? 'Ready' : 'Not yet'}`
  ].map(line => `<div class="flow-stage-card reveal-card"><div class="muted">${line}</div></div>`).join('');

  const byId = Object.fromEntries(state.oracles.map(oracle => [oracle.oracle_id, oracle]));
  const anointed = byId[state.councilStructure.anointedRuler];
  if (!selectedRulerPath && state.councilStructure.anointedRulerOptions.length) {
    selectedRulerPath = state.councilStructure.anointedRulerOptions[0].id;
  }
  document.getElementById('anointed-ruler-options').innerHTML = state.councilStructure.anointedRulerOptions.map(option => `
    <button class="data-card reveal-card ruler-option-card ${selectedRulerPath === option.id ? 'selected' : ''}" data-ruler-path="${option.id}"><strong>${option.label}</strong><div class="muted">${option.subtext}</div><div class="scene-flavor">Choose this route into the chamber.</div></button>`).join('');
  document.getElementById('anointed-ruler').innerHTML = anointed ? `<div class="data-card reveal-card threshold-card"><strong>Anointed Ruler: ${anointed.oracle_name}</strong><div class="muted">${anointed.title || anointed.archetype}</div><div class="scene-flavor">First to be created. The chamber forms around this ruling presence before the solar and lunar companions arrive.</div></div>` : '';
  document.getElementById('crowned-candidates').innerHTML = state.councilStructure.crownedCandidates.map((item, index) => `
    <div class="data-card reveal-card council-order-card summon-stage-${index + 1}"><div class="label">${summonStateLabel(index)}</div><strong>${index + 1}. ${byId[item.oracleId]?.oracle_name || item.oracleId}</strong><div class="muted">${item.reason}</div><div class="scene-flavor">${summonTone(index)}</div></div>`).join('');

  document.getElementById('chamber-return-state').textContent = state.chamberPresentation.returnState;
  const filterValue = document.getElementById('oracle-view-filter')?.value || 'all';
  const queryValue = (document.getElementById('oracle-search')?.value || '').toLowerCase();
  const filteredOracles = state.oracles.filter(oracle => {
    const matchesFilter = filterValue === 'all'
      || (filterValue === 'council' && state.councilStructure.expandedCouncil.includes(oracle.oracle_id))
      || (filterValue === 'solar' && oracle.ruling_planet === 'Sun')
      || (filterValue === 'lunar' && oracle.ruling_planet === 'Moon');
    const haystack = [oracle.oracle_name, oracle.title, oracle.archetype, oracle.ruling_planet, oracle.dominant_sign].join(' ').toLowerCase();
    return matchesFilter && (!queryValue || haystack.includes(queryValue));
  });
  const councilOrder = state.councilStructure.coreTrio;
  document.getElementById('oracle-roster').innerHTML = filteredOracles.map(oracle => {
    const orderIndex = councilOrder.indexOf(oracle.oracle_id);
    const orderLabel = orderIndex === -1 ? 'Outer chamber presence' : `Council creation order: ${orderIndex + 1}`;
    const summonLabel = summonTone(orderIndex);
    return `
    <button class="oracle-card reveal-card ${selectedOracleId === oracle.oracle_id ? 'selected' : ''}" data-oracle-id="${oracle.oracle_id}">
      <strong>${oracle.oracle_name || 'Unnamed Oracle'}</strong>
      <div class="muted">${oracle.title || oracle.archetype || 'Unformed'}</div>
      <div>${oracle.ruling_planet || '—'} • ${oracle.dominant_sign || '—'}</div>
      <div class="scene-flavor">${orderLabel}. ${summonLabel}</div>
    </button>`;
  }).join('');
  document.getElementById('current-user').innerHTML = `
    <div class="data-card reveal-card"><strong>${state.currentUser.displayName || state.currentUser.username || '—'}</strong><div class="muted">${state.currentUser.founderIdentity?.role || ''}</div><div>${state.currentUser.accountEntitlements?.tier || ''}</div></div>`;

  const activeOracle = byId[selectedOracleId];
  document.getElementById('oracle-room-prompt').textContent = state.chamberPresentation.oracleRoomPrompt;
  document.getElementById('oracle-detail').innerHTML = activeOracle ? `
    <div class="data-card reveal-card threshold-card oracle-presence-card">
      <div class="label">Oracle Presence</div><div><strong>${activeOracle.oracle_name || 'Unnamed Oracle'}</strong></div>
      <div class="muted">${activeOracle.title || activeOracle.archetype || 'Unformed'}</div>
      <div class="scene-flavor">The chamber narrows. The oracle steps into singular focus.</div>
      <div class="label" style="margin-top:10px">Celestial Mark</div><div>${activeOracle.ruling_planet || '—'} • ${activeOracle.dominant_sign || '—'} • ${activeOracle.house_placement || '—'}</div>
      <div class="label" style="margin-top:10px">Lore</div><div>${activeOracle.notes || activeOracle.mission || 'No lore recorded yet.'}</div>
    </div>` : '<div class="muted">Select an oracle.</div>';

  const commsSelect = document.getElementById('oracle-comms-select');
  commsSelect.innerHTML = state.oracles.map(oracle => `<option value="${oracle.oracle_id}">${oracle.oracle_name || oracle.oracle_id}</option>`).join('');
  if (selectedOracleId) commsSelect.value = selectedOracleId;
  document.getElementById('oracle-drafts').innerHTML = state.oracleDrafts.map(item => `
    <div class="data-card reveal-card"><strong>${byId[item.oracleId]?.oracle_name || item.oracleId}</strong><div class="muted">${item.type}</div><div>${item.message}</div></div>`).join('');

  document.getElementById('session-list').innerHTML = sessions.map(session => {
    const oracle = byId[session.oracleId];
    return `
      <button class="session-card reveal-card ${session.id === selectedSessionId ? 'selected' : ''}" data-session-id="${session.id}">
        <strong>${session.title || oracle?.oracle_name || session.id}</strong>
        <div class="muted">${session.mood || 'oracle presence'}</div>
        <div class="scene-flavor">${session.atmosphere || ''}</div>
      </button>`;
  }).join('');

  const activeSession = sessions.find(session => session.id === selectedSessionId);
  document.getElementById('oracle-room-meta').innerHTML = activeSession ? `
    <div class="data-card reveal-card threshold-card room-entry-card"><div class="label">Room Opened</div><strong>${activeSession.roomTitle || activeSession.title || activeSession.id}</strong><div class="muted">${activeSession.roomTheme || activeSession.atmosphere || ''}</div><div>${activeSession.useCase || ''}</div></div>` : '';
  document.getElementById('session-detail').innerHTML = activeSession ? activeSession.messages.map((msg, index) => `<div class="message reveal-card oracle-message-card"><div class="label">Exchange ${index + 1}</div><strong>${msg.role}:</strong> ${msg.text || msg.content}</div>`).join('') : '';

  for (const button of document.querySelectorAll('[data-scene-id]')) {
    button.addEventListener('click', () => setScene(button.dataset.sceneId));
  }
  for (const button of document.querySelectorAll('[data-ruler-path]')) {
    button.addEventListener('click', () => {
      selectedRulerPath = button.dataset.rulerPath;
      const chosen = state.councilStructure.anointedRulerOptions.find(option => option.id === selectedRulerPath);
      chamberAnnouncement = `${chosen?.label || 'A ruler path'} has been chosen. The chamber accepts your route.`;
      renderState(currentState);
    });
  }
  for (const button of document.querySelectorAll('[data-oracle-id]')) {
    button.addEventListener('click', () => {
      selectedOracleId = button.dataset.oracleId;
      unlockScene(state, 'chamber-hub');
      unlockScene(state, 'oracle-room');
      chamberAnnouncement = `${byId[button.dataset.oracleId]?.oracle_name || 'An oracle'} has stepped forward. The room opens.`;
      state.progressionState.completedScenes = Array.from(new Set([...state.progressionState.completedScenes, 'title-screen', 'first-entrance', 'chart-awakening', 'council-formation', 'chamber-hub']));
      state.progressionState.nextRecommendedScene = 'oracle-room';
      setScene('oracle-room');
      renderState(currentState);
    });
  }
  for (const button of document.querySelectorAll('[data-session-id]')) {
    button.addEventListener('click', () => {
      selectedSessionId = button.dataset.sessionId;
      renderState(currentState);
    });
  }

  setScene(currentScene);
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
      await api('/api/oracle-draft', { oracleId: commsSelect.value, message: commsMessage.value, type: 'draft' });
      commsMessage.value = '';
      load();
    });
  }
  if (logBtn && !logBtn.dataset.bound) {
    logBtn.dataset.bound = 'true';
    logBtn.addEventListener('click', async () => {
      await api('/api/oracle-note', { oracleId: commsSelect.value, message: commsMessage.value });
      commsMessage.value = '';
      load();
    });
  }
}

load();