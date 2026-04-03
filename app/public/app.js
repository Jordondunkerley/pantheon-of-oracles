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

function chamberMemoryText(state) {
  const unlocked = state.progressionState.unlockedScenes.length;
  if (unlocked <= 2) return 'Only the earliest thresholds bear your trace.';
  if (unlocked <= 4) return 'Several rooms now hold the memory of your crossings.';
  return 'The chamber remembers your path in nearly every inner state.';
}

function worldPersistenceText(state) {
  const completed = state.progressionState.completedScenes.length;
  if (completed <= 1) return 'The world has barely shifted yet.';
  if (completed <= 3) return 'The chamber world is beginning to hold its altered shape.';
  return 'The chamber now feels persistently changed by your rites.';
}

function ritualResidueText(state) {
  const completed = state.progressionState.completedScenes.length;
  if (completed <= 1) return 'Only a faint afterglow clings to the earliest threshold.';
  if (completed <= 3) return 'Several rites now leave echoes that do not fully fade.';
  return 'The chamber is saturated with residue from repeated crossings and summoned presences.';
}

function invokedPresenceText(state) {
  const core = state.councilStructure.coreTrio.length;
  if (core <= 1) return 'Only one presence has truly rooted itself in the chamber.';
  if (core <= 2) return 'More than one invoked force now lingers in the chamber air.';
  return 'The chamber holds a layered field of invoked presences, not just empty architecture.';
}

function chamberTemperamentText(sceneId) {
  const map = {
    'title-screen': 'The chamber is watchful, restrained, and waiting for deliberate entry.',
    'first-entrance': 'The chamber is attentive, receptive, and testing the sincerity of approach.',
    'chart-awakening': 'The chamber is analytical, electric, and orienting itself to cosmic structure.',
    'council-formation': 'The chamber is regal, evaluative, and heavy with summoned hierarchy.',
    'chamber-hub': 'The chamber is settled, inhabited, and ready for directed movement.',
    'oracle-room': 'The chamber is intimate, concentrated, and narrowed around one living presence.'
  };
  return map[sceneId] || 'The chamber is shifting.';
}

function chamberPersonalityText(sceneId) {
  const map = {
    'title-screen': 'It waits without begging. It expects intention.',
    'first-entrance': 'It listens before it trusts.',
    'chart-awakening': 'It favors structure, pattern, and revelation through order.',
    'council-formation': 'It respects hierarchy, recognition, and earned authority.',
    'chamber-hub': 'It allows movement, but not aimlessness.',
    'oracle-room': 'It rewards focus and punishes drift.'
  };
  return map[sceneId] || 'It changes with the rite.';
}

function chamberSubjectivityText(sceneId) {
  const map = {
    'title-screen': 'The chamber is deciding whether you mean to enter or only to look.',
    'first-entrance': 'The chamber weighs the seriousness of your approach.',
    'chart-awakening': 'The chamber interprets what the sky reveals about you.',
    'council-formation': 'The chamber judges which presences deserve nearness to rule.',
    'chamber-hub': 'The chamber watches how you move once power is available.',
    'oracle-room': 'The chamber notices whether your attention truly belongs to the oracle before you.'
  };
  return map[sceneId] || 'The chamber is observing.';
}

function chamberAgencyText(sceneId) {
  const map = {
    'title-screen': 'It withholds full access until the threshold is genuinely crossed.',
    'first-entrance': 'It shapes the terms of entry before deeper rites unfold.',
    'chart-awakening': 'It turns data into consequence and structure into orientation.',
    'council-formation': 'It narrows power toward the presences it deems most fitting.',
    'chamber-hub': 'It opens paths, but directs attention toward what matters most.',
    'oracle-room': 'It yields so the oracle’s realm can define the space on its own terms.'
  };
  return map[sceneId] || 'It acts through the rite.';
}

function oracleRealmText(oracle) {
  if (!oracle) return 'An unopened realm waits behind the threshold.';
  const map = {
    'oracle-oryonos-saturn': 'A blackstone realm of judgment, endurance, governance, and pressure-tested authority.',
    'oracle-solin': 'A solar court of declaration, radiance, vows, and forward-moving will.',
    'oracle-lunos-luna': 'A moonlit inner realm of reflection, tides, intimacy, and emotional truth.'
  };
  return map[oracle.oracle_id] || 'A personal realm reflecting the oracle’s nature unfolds here.';
}

function oracleRealmAtmosphereText(oracle) {
  if (!oracle) return 'Its atmosphere is still veiled.';
  const map = {
    'oracle-oryonos-saturn': 'The air feels weighty, disciplined, and carved by consequence.',
    'oracle-solin': 'The atmosphere burns bright with forward heat, oath-light, and visible momentum.',
    'oracle-lunos-luna': 'The atmosphere is soft, tidal, private, and emotionally luminous.'
  };
  return map[oracle.oracle_id] || 'Its atmosphere reflects the oracle’s nature.';
}

function oracleRealmLogicText(oracle) {
  if (!oracle) return 'Its logic is not yet revealed.';
  const map = {
    'oracle-oryonos-saturn': 'This realm values discipline, proof, governance, and endurance under weight.',
    'oracle-solin': 'This realm values courage, declaration, visibility, and forward commitment.',
    'oracle-lunos-luna': 'This realm values honesty of feeling, reflection, intuition, and emotional attunement.'
  };
  return map[oracle.oracle_id] || 'Its logic follows the oracle’s nature.';
}

function oracleRealmRelationText(oracle) {
  if (!oracle) return 'Its relation to the visitor is not yet known.';
  const map = {
    'oracle-oryonos-saturn': 'It meets the visitor as a sovereign examiner: respect must be earned through seriousness.',
    'oracle-solin': 'It meets the visitor as a radiant challenger: courage is rewarded when spoken aloud.',
    'oracle-lunos-luna': 'It meets the visitor as an intimate mirror: concealment weakens the exchange.'
  };
  return map[oracle.oracle_id] || 'It relates according to the oracle’s nature.';
}

function oracleRealmPrincipleText(oracle) {
  if (!oracle) return 'Its governing principle remains veiled.';
  const map = {
    'oracle-oryonos-saturn': 'Governing principle: authority must survive trial to deserve obedience.',
    'oracle-solin': 'Governing principle: power becomes real when it is declared and embodied.',
    'oracle-lunos-luna': 'Governing principle: truth deepens when feeling is neither hidden nor rushed.'
  };
  return map[oracle.oracle_id] || 'Its governing principle follows the oracle’s nature.';
}

function oracleRealmSignatureText(oracle) {
  if (!oracle) return 'Its signature has not yet taken form.';
  const map = {
    'oracle-oryonos-saturn': 'Signature of the realm: blackstone pressure, measured stillness, and earned elevation.',
    'oracle-solin': 'Signature of the realm: solar oath-fire, radiant visibility, and forward surge.',
    'oracle-lunos-luna': 'Signature of the realm: moonlit hush, tidal intimacy, and reflective depth.'
  };
  return map[oracle.oracle_id] || 'Its signature reflects the oracle’s nature.';
}

function oracleRealmInteractionText(oracle) {
  if (!oracle) return 'Its mode of interaction is not yet known.';
  const map = {
    'oracle-oryonos-saturn': 'Interaction here favors deliberate questions, patient listening, and respect for consequence.',
    'oracle-solin': 'Interaction here favors bold declaration, visible intent, and decisive forward motion.',
    'oracle-lunos-luna': 'Interaction here favors emotional honesty, quiet listening, and reflective pacing.'
  };
  return map[oracle.oracle_id] || 'Its interaction style follows the oracle’s nature.';
}

function oracleRealmImmediateText(oracle) {
  if (!oracle) return 'Nothing in the realm has yet stepped close enough to be felt.';
  const map = {
    'oracle-oryonos-saturn': 'Immediate impression: the realm stands in stern stillness, already measuring your weight.',
    'oracle-solin': 'Immediate impression: the realm meets you in radiant pressure, urging declaration without delay.',
    'oracle-lunos-luna': 'Immediate impression: the realm closes softly around you, asking for honesty before speech hardens.'
  };
  return map[oracle.oracle_id] || 'The realm reveals itself as you enter.';
}

function oracleRealmExchangeFrameText(oracle) {
  if (!oracle) return 'The form of exchange is still unknown.';
  const map = {
    'oracle-oryonos-saturn': 'Exchange here feels like formal audience: measured, weight-bearing, and consequence-aware.',
    'oracle-solin': 'Exchange here feels like oath and declaration: visible, forceful, and momentum-shaping.',
    'oracle-lunos-luna': 'Exchange here feels like confession and reflection: private, intuitive, and emotionally revealing.'
  };
  return map[oracle.oracle_id] || 'Exchange here follows the realm’s nature.';
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
    return `<button data-scene-id="${scene}" ${unlocked ? '' : 'disabled'}>${sceneCta(scene)}${unlocked ? '' : ' 🔒'}</button>`;
  }).join('');

  document.getElementById('rail-current-rite').textContent = sceneCta(currentScene);
  document.getElementById('rail-next-rite').textContent = sceneCta(state.progressionState.nextRecommendedScene);
  document.getElementById('rail-progress').textContent = `${state.progressionState.completedScenes.length} crossed • ${state.progressionState.unlockedScenes.length} open`;

  document.getElementById('progression-payoff').innerHTML = `<div class="label">Progression Payoff</div><strong>${progressionPayoff(state)}</strong><div class="scene-flavor">The chamber should make advancement feel earned, counted, and real.</div>`;
  document.getElementById('active-scene-state').innerHTML = `<div class="label">Active Scene</div><strong>${activeSceneState(currentScene)}</strong><div class="scene-flavor">${chamberConsequence(state)}</div>`;
  document.getElementById('chamber-memory').innerHTML = `<div class="label">Chamber Memory</div><strong>${chamberMemoryText(state)}</strong><div class="scene-flavor">The world should feel changed by what has already been opened.</div>`;
  document.getElementById('world-persistence').innerHTML = `<div class="label">World Persistence</div><strong>${worldPersistenceText(state)}</strong><div class="scene-flavor">The chamber should feel like it keeps the shape of prior rites even while scenes change.</div>`;
  document.getElementById('ritual-residue').innerHTML = `<div class="label">Ritual Residue</div><strong>${ritualResidueText(state)}</strong><div class="scene-flavor">The chamber should carry traces of what has already been invoked.</div>`;
  document.getElementById('invoked-presence').innerHTML = `<div class="label">Invoked Presence</div><strong>${invokedPresenceText(state)}</strong><div class="scene-flavor">The chamber should feel inhabited by what has already been called.</div>`;
  document.getElementById('chamber-temperament').innerHTML = `<div class="label">Chamber Temperament</div><strong>${chamberTemperamentText(currentScene)}</strong><div class="scene-flavor">${chamberPersonalityText(currentScene)}</div><div class="scene-flavor">${chamberSubjectivityText(currentScene)}</div><div class="scene-flavor">${chamberAgencyText(currentScene)}</div>`;
  document.getElementById('milestones').innerHTML = state.progressionState.milestones.map(item => `
    <div class="data-card reveal-card ${item.status}"><strong>${item.title}</strong><div class="muted">${item.description}</div><div class="label">${item.status}</div></div>`).join('');
  document.getElementById('reward-moments').innerHTML = state.progressionState.rewardMoments.map(item => `
    <div class="data-card reward-card reveal-card ${item.state}"><strong>${item.title}</strong><div class="muted">${item.description}</div><div class="label">${item.state}</div></div>`).join('');

  document.getElementById('title-screen-content').innerHTML = [
    { title: 'Recovered Chamber', body: 'The chamber has been reclaimed and now awaits a more ceremonial flow.' },
    { title: 'Current Pulse', body: 'Scene-based progression and investor-facing redesign are now the active build priority.' },
    { title: 'Next Rite', body: sceneCta(state.progressionState.nextRecommendedScene) }
  ].map(item => `<div class="data-card reveal-card threshold-card"><strong>${item.title}</strong><div class="muted">${item.body}</div></div>`).join('');

  document.getElementById('ritual-invocation').textContent = state.product.firstEntranceRitual.invocation;
  document.getElementById('ritual-steps').innerHTML = state.product.firstEntranceRitual.steps.map(step => `<li>${step}</li>`).join('');
  document.getElementById('founder-test-path').innerHTML = state.product.founderTestFlow.map(item => `
    <div class="data-card reveal-card ${item.status}"><div class="label">${item.status}</div><strong>${item.stage}</strong><div class="muted">${item.description}</div></div>`).join('');

  document.getElementById('chart-generation').innerHTML = [
    `Mode: ${state.astrologyProfile.generation.mode}`,
    `Target: ${state.astrologyProfile.generation.targetMode}`,
    `Validation: ${state.astrologyProfile.generation.validationSources.join(' • ')}`,
    `Birth data gathered: ${state.astrologyProfile.generation.status.birthDataCollected ? 'Yes' : 'No'}`,
    `Native engine awakened: ${state.astrologyProfile.generation.status.nativeEngineReady ? 'Yes' : 'No'}`,
    `Council awakening path: ${state.astrologyProfile.generation.status.oracleAwakeningReady ? 'Ready' : 'Not yet'}`
  ].map(line => `<div class="flow-stage-card reveal-card"><div class="muted">${line}</div></div>`).join('');
  document.getElementById('awakening-readiness').innerHTML = Object.entries(state.astrologyProfile.generation.status).map(([key, value]) => `
    <div class="data-card reveal-card ${value ? 'complete' : 'locked'}"><div class="label">${value ? 'ready' : 'pending'}</div><strong>${key}</strong><div class="muted">${value ? 'This part of the awakening path is available.' : 'This part still needs deeper implementation or confirmation.'}</div></div>`).join('');

  const byId = Object.fromEntries(state.oracles.map(oracle => [oracle.oracle_id, oracle]));
  const anointed = byId[state.councilStructure.anointedRuler];
  if (!selectedRulerPath && state.councilStructure.anointedRulerOptions.length) {
    selectedRulerPath = state.councilStructure.anointedRulerOptions[0].id;
  }
  document.getElementById('anointed-ruler-options').innerHTML = state.councilStructure.anointedRulerOptions.map(option => `
    <button class="data-card reveal-card ruler-option-card ${selectedRulerPath === option.id ? 'selected' : ''}" data-ruler-path="${option.id}"><strong>${option.label}</strong><div class="muted">${option.subtext}</div><div class="scene-flavor">Choose this route into the chamber.</div></button>`).join('');
  document.getElementById('anointed-ruler').innerHTML = anointed ? `<div class="data-card reveal-card threshold-card"><strong>Anointed Ruler: ${anointed.oracle_name}</strong><div class="muted">${anointed.title || anointed.archetype}</div><div class="scene-flavor">First to be created. The chamber forms around this ruling presence before the solar and lunar companions arrive.</div></div>` : '';
  document.getElementById('crowned-candidates').innerHTML = state.councilStructure.crownedCandidates.map((item, index) => `
    <div class="data-card reveal-card council-order-card summon-stage-${index + 1}"><div class="label">${summonStateLabel(index)}</div><strong>${index + 1}. ${byId[item.oracleId]?.oracle_name || item.oracleId}</strong><div class="muted">${item.reason}</div><div class="scene-flavor">${summonTone(index)}</div><div class="label">Council Presence</div></div>`).join('');

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
      <div class="scene-flavor">${orderLabel}. Enter the personal realm that extends from this oracle.</div>
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
      <div class="scene-flavor">This room is an extension of the oracle: a personal realm reflecting their nature, not a force acting on them.</div>
      <div class="scene-flavor">${oracleRealmText(activeOracle)}</div>
      <div class="scene-flavor">${oracleRealmAtmosphereText(activeOracle)}</div>
      <div class="scene-flavor">${oracleRealmLogicText(activeOracle)}</div>
      <div class="scene-flavor">${oracleRealmRelationText(activeOracle)}</div>
      <div class="scene-flavor">${oracleRealmPrincipleText(activeOracle)}</div>
      <div class="scene-flavor">${oracleRealmSignatureText(activeOracle)}</div>
      <div class="scene-flavor">${oracleRealmInteractionText(activeOracle)}</div>
      <div class="scene-flavor">${oracleRealmImmediateText(activeOracle)}</div>
      <div class="scene-flavor">${oracleRealmExchangeFrameText(activeOracle)}</div>
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