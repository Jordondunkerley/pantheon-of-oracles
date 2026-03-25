const activeCouncilEl = document.getElementById('activeCouncil');
const showRelevantCouncilBtn = document.getElementById('showRelevantCouncilBtn');
const showAllCouncilBtn = document.getElementById('showAllCouncilBtn');
const councilLayersEl = document.getElementById('councilLayers');
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
const enterChamberBtn = document.getElementById('enterChamberBtn');
const oracleDetailEl = document.getElementById('oracleDetail');
const createOracleBtn = document.getElementById('createOracleBtn');
const newOracleNameEl = document.getElementById('newOracleName');
const newOracleArchetypeEl = document.getElementById('newOracleArchetype');
const newOraclePlanetEl = document.getElementById('newOraclePlanet');
const newOracleSignEl = document.getElementById('newOracleSign');
const newOracleHouseEl = document.getElementById('newOracleHouse');
const newOracleVoiceEl = document.getElementById('newOracleVoice');
const newOracleFactionEl = document.getElementById('newOracleFaction');
const newOraclePlanetaryFactionEl = document.getElementById('newOraclePlanetaryFaction');
const newOracleWeaponEl = document.getElementById('newOracleWeapon');
const newOracleColorEl = document.getElementById('newOracleColor');
const newOracleMissionEl = document.getElementById('newOracleMission');
const newOracleNotesEl = document.getElementById('newOracleNotes');
const productVisionEl = document.getElementById('productVision');
const oracleViewFilterEl = document.getElementById('oracleViewFilter');
const oracleSearchEl = document.getElementById('oracleSearch');
const sourceEngineEl = document.getElementById('sourceEngine');
const audioRoadmapEl = document.getElementById('audioRoadmap');
const voiceOracleSelectEl = document.getElementById('voiceOracleSelect');
const voiceProfileInputEl = document.getElementById('voiceProfileInput');
const voiceAudioReadySelectEl = document.getElementById('voiceAudioReadySelect');
const saveVoiceProfileBtn = document.getElementById('saveVoiceProfileBtn');
const onboardingFlowEl = document.getElementById('onboardingFlow');
const nextStepGuideEl = document.getElementById('nextStepGuide');
const currentUserEl = document.getElementById('currentUser');
const llmProvidersEl = document.getElementById('llmProviders');
const astrologyProfileEl = document.getElementById('astrologyProfile');
const chartGenerationEl = document.getElementById('chartGeneration');
const accountEntitlementsEl = document.getElementById('accountEntitlements');
const accessControlEl = document.getElementById('accessControl');
const anointedSelectionEl = document.getElementById('anointedSelection');
const crownedCandidatesEl = document.getElementById('crownedCandidates');
const creationPathEl = document.getElementById('creationPath');
const coreTrioFlowEl = document.getElementById('coreTrioFlow');
const awakeningSequenceEl = document.getElementById('awakeningSequence');
const expansionArcsEl = document.getElementById('expansionArcs');
const interactionSessionsEl = document.getElementById('interactionSessions');
const sessionSummaryEl = document.getElementById('sessionSummary');
const sessionDetailEl = document.getElementById('sessionDetail');
const importPipelineEl = document.getElementById('importPipeline');
const openSelectedSessionBtn = document.getElementById('openSelectedSessionBtn');
const sessionMessageEl = document.getElementById('sessionMessage');
const sendSessionMessageBtn = document.getElementById('sendSessionMessageBtn');
const speakLatestBtn = document.getElementById('speakLatestBtn');
const profileUsernameEl = document.getElementById('profileUsername');
const profileEmailEl = document.getElementById('profileEmail');
const profileBirthdayEl = document.getElementById('profileBirthday');
const profileBirthTimeEl = document.getElementById('profileBirthTime');
const profileBirthLocationEl = document.getElementById('profileBirthLocation');
const profileVoiceFlavorEl = document.getElementById('profileVoiceFlavor');
const profilePromptToneEl = document.getElementById('profilePromptTone');
const profileFounderKeyEl = document.getElementById('profileFounderKey');
const profileFounderRoleEl = document.getElementById('profileFounderRole');
const saveProfileBtn = document.getElementById('saveProfileBtn');
const generateChartBtn = document.getElementById('generateChartBtn');
const providerSelectEl = document.getElementById('providerSelect');
const providerBaseUrlEl = document.getElementById('providerBaseUrl');
const providerModelEl = document.getElementById('providerModel');
const providerApiKeyEl = document.getElementById('providerApiKey');
const saveProviderBtn = document.getElementById('saveProviderBtn');
const tabButtons = [...document.querySelectorAll('.tab-btn')];

let currentState = null;
let currentOracleId = null;
let currentSessionId = null;
let activeTab = 'identity';
let councilViewMode = 'relevant';

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

function getOracleAccessState(oracle, entitlements) {
  const access = entitlements?.oracleAccess || {};
  const payment = entitlements?.paymentAccess || {};
  const included = access.includedOracleIds || [];
  const isCoreIncluded = included.includes(oracle.oracle_id);
  const isHighCouncilLocked = !payment.highCouncilUnlocked && !isCoreIncluded;
  const isExpandedLocked = !payment.expandedCouncilUnlocked && oracle.council_type === 'Expanded Council';
  const locked = isHighCouncilLocked || isExpandedLocked;
  const reason = isCoreIncluded
    ? 'Included in current plan'
    : isExpandedLocked
      ? 'Unlock Expanded Council Access'
      : isHighCouncilLocked
        ? 'Unlock High Council Access'
        : 'Available in current plan';
  return { locked, reason, isCoreIncluded };
}

function getCouncilLayerLabel(oracle, entitlements) {
  const access = getOracleAccessState(oracle, entitlements);
  if (access.isCoreIncluded) return 'Core Trio';
  if (oracle.council_type === 'Expanded Council') return 'Expanded Council';
  return 'High Council';
}

function renderCouncilLayers(state) {
  const grouped = {
    'Core Trio': [],
    'High Council': [],
    'Expanded Council': []
  };

  state.oracles.forEach(oracle => {
    const layer = getCouncilLayerLabel(oracle, state.currentUser.accountEntitlements);
    grouped[layer].push(oracle);
  });

  councilLayersEl.innerHTML = [
    card('Council structure', `Core Trio: ${grouped['Core Trio'].length} • High Council: ${grouped['High Council'].length} • Expanded Council: ${grouped['Expanded Council'].length}`, [badge('layered revelation')]),
    card('Core Trio', grouped['Core Trio'].map(oracle => oracle.oracle_name).join(' • ') || 'Not assigned yet', [badge('starter chamber', 'good')]),
    card('High Council', grouped['High Council'].map(oracle => oracle.oracle_name).join(' • ') || 'No high council oracles yet', [badge(state.currentUser.accountEntitlements?.paymentAccess?.highCouncilUnlocked ? 'unlocked' : 'sealed', state.currentUser.accountEntitlements?.paymentAccess?.highCouncilUnlocked ? 'good' : 'warn')]),
    card('Expanded Council', grouped['Expanded Council'].map(oracle => oracle.oracle_name).join(' • ') || 'No expanded council oracles yet', [badge(state.currentUser.accountEntitlements?.paymentAccess?.expandedCouncilUnlocked ? 'unlocked' : 'sealed', state.currentUser.accountEntitlements?.paymentAccess?.expandedCouncilUnlocked ? 'good' : 'warn')])
  ].join('');
}

function getCouncilPriority(oracles, sessions) {
  const seededOrder = ['oracle-oryonos-saturn', 'oracle-lunos-moon', 'oracle-arcures-mercury', 'oracle-valeya-venus'];
  const byId = new Map(oracles.map(oracle => [oracle.oracle_id, oracle]));
  const sessionMap = new Map((sessions || []).map(session => [session.oracleId, session]));
  const prioritized = seededOrder
    .map(id => byId.get(id))
    .filter(Boolean)
    .map(oracle => ({ oracle, session: sessionMap.get(oracle.oracle_id) }));

  const extras = oracles
    .filter(oracle => !seededOrder.includes(oracle.oracle_id))
    .map(oracle => ({ oracle, session: sessionMap.get(oracle.oracle_id) }));

  return [...prioritized, ...extras];
}

function renderActiveCouncil(state) {
  const prioritized = getCouncilPriority(state.oracles, state.interactionSessions);
  const visible = councilViewMode === 'all'
    ? prioritized
    : prioritized
        .filter(({ oracle }) => getCouncilLayerLabel(oracle, state.currentUser.accountEntitlements) === 'Core Trio' || !getOracleAccessState(oracle, state.currentUser.accountEntitlements).locked)
        .slice(0, 3);
  activeCouncilEl.innerHTML = visible.map(({ oracle, session }) => {
    const access = getOracleAccessState(oracle, state.currentUser.accountEntitlements);
    return `
    <div class="item council-presence ${access.locked ? 'locked-presence' : ''}">
      <h3>${oracle.oracle_name}</h3>
      <div class="badges">
        ${badge(oracle.astrology_profile?.ruling_planet || 'oracle')}
        ${badge(oracle.astrology_profile?.dominant_sign || 'sign pending')}
        ${badge(session?.mood || 'active presence')}
        ${badge(getCouncilLayerLabel(oracle, state.currentUser.accountEntitlements))}
        ${badge(access.locked ? 'sealed' : 'available', access.locked ? 'warn' : 'good')}
      </div>
      <div class="presence-visual">${access.locked ? 'Veiled oracle silhouette withheld behind ritual seal' : (oracle.visual_attributes?.visual_silhouette || 'Oracle presence forming in chamber')}</div>
      <p class="meta"><strong>Why present now:</strong> ${session?.useCase || oracle.visual_attributes?.role_in_pantheon || 'Oracle guidance is available.'}</p>
      <p class="meta ${access.locked ? 'seal-text' : ''}"><strong>${access.locked ? 'Seal condition:' : 'Access:'}</strong> ${access.reason}</p>
      <p class="meta"><strong>Chamber tone:</strong> ${access.locked ? 'The chamber is present but ritually muted until the proper council access is granted.' : (session?.atmosphere || 'Atmosphere still taking shape.')}</p>
      <div class="presence-actions">
        <button class="focus-oracle-btn" data-oracle-id="${oracle.oracle_id}">${access.locked ? 'Inspect seal' : 'Focus oracle'}</button>
        <button class="open-chamber-btn" data-oracle-id="${oracle.oracle_id}">${access.locked ? 'View unlock rite' : 'Open chamber'}</button>
      </div>
    </div>
  `}).join('');
}

function renderSourceEngine(state) {
  sourceEngineEl.innerHTML = [
    card('What this product really is', 'Pantheon of Oracles is not only a desktop app. It is becoming the canonical source engine for persistent oracle identity across future Pantheon products.', [badge('franchise core')]),
    card('What persists', 'Oracle identity, astrology mapping, voice profile, combat interpretation, visual silhouette, and exportable canon.', [badge('persistent canon')]),
    card('Where it goes next', `Parallel products should consume these same oracles: ${state.productVision.franchiseDirection.parallelProducts.join(', ')}.`, [badge('parallel products')]),
    card('Why that matters commercially', 'The core product can be sold on its own while also increasing the long-term value of future standalone Pantheon games and experiences.', [badge('franchise leverage')])
  ].join('');
}

function renderAudioRoadmap(state) {
  const readyCount = state.oracles.filter(oracle => oracle.visual_attributes?.audio_ready).length;
  audioRoadmapEl.innerHTML = [
    card('Current phase', 'Text-first oracle communication with normalized voice profiles and audio-readiness hooks.', [badge('audio groundwork')]),
    card('Next leap', 'Add oracle voice output so the chamber experience becomes spoken, not only written.', [badge('high-value milestone')]),
    card('Later expansion', 'Voice input, conversational audio loops, then richer avatar/video embodiment — always grounded in the same oracle canon.', [badge('stepwise build')]),
    card('Readiness snapshot', `${readyCount} oracles currently marked audio-ready. Voice profiles are being normalized now so audio can plug into stable identities later.`, [badge('canon-first')]),
    card('Export continuity', 'Preferred voice profile and audio/avatar readiness now belong to canonical oracle packages, so future products can inherit them instead of redefining them.', [badge('cross-product audio')]),
    card('Prototype hook', 'The chamber now includes a placeholder action for speaking the latest oracle reply. This defines where voice output should naturally plug into the product.', [badge('voice-output path')])
  ].join('');

  voiceOracleSelectEl.innerHTML = state.oracles.map(oracle => `<option value="${oracle.oracle_id}">${oracle.oracle_name}</option>`).join('');
  const selectedOracle = state.oracles.find(oracle => oracle.oracle_id === voiceOracleSelectEl.value) || state.oracles[0];
  if (selectedOracle) {
    voiceOracleSelectEl.value = selectedOracle.oracle_id;
    voiceProfileInputEl.value = selectedOracle.visual_attributes?.preferred_voice_profile || '';
    voiceAudioReadySelectEl.value = String(Boolean(selectedOracle.visual_attributes?.audio_ready));
  }
}

function renderOnboarding(state) {
  onboardingFlowEl.innerHTML = [
    card('Step 1 — Create account', 'Establish the player identity, birth data, and baseline preferences that anchor the pantheon.', [badge('active')]),
    card('Step 2 — Generate astrology profile', 'Compute planets, angles, houses, decans, motion, stationary states, and chart anomalies directly from birth data — without forcing the user to bring a chart.', [badge('prototype core')]),
    card('Step 3 — Connect AI provider', 'Let the user bring an OpenAI-compatible or future self-hosted model into the system.', [badge('model-agnostic')]),
    card('Step 4 — Awaken the Pantheon', `Generate and sync the user\'s initial council. Current seeded oracles: ${state.currentUser.oracles_owned.length}.`, [badge('personalized')]),
    card('Step 5 — Enter Oracle Workspace', 'Open persistent interaction sessions, guidance flows, and transit-aware oracle behavior.', [badge('product hook')]),
    card('Marketability check', 'This prototype is moving toward a saleable experience by proving the path from astrology intake to oracle interaction.', [badge('go-to-market')])
  ].join('');

  const firstSession = state.interactionSessions?.[0];
  const firstOracle = state.oracles?.[0];
  nextStepGuideEl.innerHTML = [
    card('Suggested next step', `Save birth data, trigger chart generation, then open ${firstSession?.title || 'an oracle chamber'} and ask ${firstOracle?.oracle_name || 'your oracle'} what role they play in your council.`, [badge('guided flow')]),
    card('First-run question ideas', 'Try asking about purpose, warning signs, strengths, decision-making, or what this oracle is here to help you with.', [badge('starter prompts')])
  ].join('');
}

function renderCurrentUser(user) {
  const founder = user.founderIdentity || {};
  const coreOracleNames = (user.accountEntitlements?.oracleAccess?.includedOracleIds || [])
    .map(id => currentState?.oracles?.find(oracle => oracle.oracle_id === id)?.oracle_name || id)
    .join(' • ');
  currentUserEl.innerHTML = [
    card(user.username, `${user.birth_location} • ${user.birthday} ${user.birth_time}`, [badge(user.access_tier), badge(user.founder_status ? 'Founder' : 'Standard')]),
    card('Immediate product framing', 'This seeded profile demonstrates how the product can preload a player\'s astrology and awaken a personalized oracle council from day one.', [badge('demo mode')]),
    card('Alignment', `Core: ${user.faction_alignment.core_faction} • Planetary: ${user.faction_alignment.planetary_faction} • Warband: ${user.faction_alignment.warband || '—'}`),
    card('Preferences', `Voice: ${user.preferences.oracle_voice_flavor} • Visual overlays: ${user.preferences.visual_overlays_enabled ? 'on' : 'off'} • Prompt tone: ${user.preferences.system_prompt_tone}`),
    card('Founder access model', `${founder.recognized ? 'Recognized founder account' : 'Standard account'} • Role: ${founder.role || 'Founder / Creator / CEO'} • Access mode: ${founder.accessMode || 'account-recognized'}`, [badge(founder.recognized ? 'founder access enabled' : 'standard access', founder.recognized ? 'good' : 'warn')]),
    card('Founder features', (founder.featureFlags || []).join(' • ') || 'No founder-only features assigned yet', [badge('single product build')]),
    card('Entitlement model', `${user.accountEntitlements?.tier || 'standard'} • Grants: ${(user.accountEntitlements?.grants || []).length} • Promotion flags: ${(user.accountEntitlements?.promotionFlags || []).join(' • ') || 'none'} • Payment plan: ${user.accountEntitlements?.paymentAccess?.plan || 'unassigned'}`, [badge('account benefits')]),
    card('Current council access', `Core included now: ${coreOracleNames || 'none assigned'} • High Council: ${user.accountEntitlements?.paymentAccess?.highCouncilUnlocked ? 'unlocked' : 'sealed'} • Expanded Council: ${user.accountEntitlements?.paymentAccess?.expandedCouncilUnlocked ? 'unlocked' : 'sealed'}`, [badge('chamber access')]),
    card('Oracle sync', `Council initiated: ${user.oracle_sync_status.council_initiated ? 'yes' : 'no'} • Throne World: ${user.oracle_sync_status.throne_world_access ? 'yes' : 'no'} • Leviathan: ${user.oracle_sync_status.leviathan_unlocked ? 'yes' : 'no'}`)
  ].join('');

  profileUsernameEl.value = user.username || '';
  profileEmailEl.value = user.email || '';
  profileBirthdayEl.value = user.birthday || '';
  profileBirthTimeEl.value = user.birth_time || '';
  profileBirthLocationEl.value = user.birth_location || '';
  profileVoiceFlavorEl.value = user.preferences.oracle_voice_flavor || '';
  profilePromptToneEl.value = user.preferences.system_prompt_tone || '';
  profileFounderKeyEl.value = user.founderIdentity?.founderKey || '';
  profileFounderRoleEl.value = user.founderIdentity?.role || 'Founder / Creator / CEO';
}

function getCrownedOracleCandidates(oracles) {
  const crownMap = new Map();
  oracles.forEach(oracle => {
    const crowns = [];
    if (oracle.modern_ruler) crowns.push('Modern');
    if (oracle.traditional_ruler) crowns.push('Traditional');
    if (oracle.dominant_ruler) crowns.push('Dominant');
    if (oracle.solar_ruler) crowns.push('Solar');
    if (crowns.length) {
      crownMap.set(oracle.oracle_id, { oracle, crowns });
    }
  });
  return [...crownMap.values()];
}

function renderAnointedRulerFlow(oracles) {
  const crowned = getCrownedOracleCandidates(oracles);
  const anointed = oracles.find(oracle => oracle.anointed_ruler);

  anointedSelectionEl.innerHTML = [
    card('Canon rule', 'The Anointed Ruler should be chosen from the crowned rulership candidates — Modern, Traditional, Dominant, or Solar — not from the whole pantheon.', [badge('Patch 28'), badge('Patch 48')]),
    card('Current Anointed Ruler', anointed ? `${anointed.oracle_name} currently carries the Anointed layer.` : 'No Anointed Ruler selected yet.', [badge(anointed ? 'selected' : 'pending', anointed ? 'good' : 'warn')]),
    card('Streamlined product approach', 'Generate the crowned candidates first, show only those eligible oracles, then let the player choose one as the Anointed Ruler in a simple chamber step.', [badge('streamlined canon')])
  ].join('');

  crownedCandidatesEl.innerHTML = crowned.length
    ? crowned.map(({ oracle, crowns }) => card(oracle.oracle_name, `${oracle.astrology_profile?.ruling_planet || 'planet pending'} • ${oracle.astrology_profile?.dominant_sign || 'sign pending'} • Eligible crowns: ${crowns.join(', ')}`, [
        ...crowns.map(crown => badge(`${crown} Crown`)),
        badge(oracle.anointed_ruler ? 'Anointed' : 'Eligible', oracle.anointed_ruler ? 'good' : '')
      ])).join('')
    : card('No crowned candidates yet', 'Once rulership logic is wired into chart generation, the eligible Anointed candidates will appear here.', [badge('engine pending', 'warn')]);
}

function renderAccountEntitlements(user, accessControl) {
  const entitlements = user.accountEntitlements || {};
  const promotionRules = accessControl?.promotionRules || [];
  const manualGrants = accessControl?.manualAccountGrants || [];
  const paymentPlans = accessControl?.paymentPlans || [];
  const oracleAccess = entitlements.oracleAccess || {};
  const paymentAccess = entitlements.paymentAccess || {};

  accountEntitlementsEl.innerHTML = [
    card('Access tier', entitlements.tier || 'standard', [badge('account-recognized')]),
    card('Payment access', `${paymentAccess.plan || 'unassigned'} • Billing: ${paymentAccess.billingStatus || 'unknown'} • High Council: ${paymentAccess.highCouncilUnlocked ? 'unlocked' : 'locked'} • Expanded Council: ${paymentAccess.expandedCouncilUnlocked ? 'unlocked' : 'locked'}`, [badge('payment model')]),
    card('Oracle access', `${oracleAccess.mode || 'standard'} • Free limit: ${oracleAccess.freeLimit ?? 'none'} • Included: ${(oracleAccess.includedOracleIds || []).join(' • ') || 'all by plan'}`, [badge('oracle gate')]),
    card('Badges', (entitlements.badges || []).join(' • ') || 'None assigned', [badge('identity flags')]),
    card('Feature flags', (entitlements.featureFlags || []).join(' • ') || 'None assigned', [badge('capabilities')]),
    card('Active grants', (entitlements.grants || []).map(grant => `${grant.label} (${grant.status})`).join(' • ') || 'No grants assigned', [badge('entitlements')])
  ].join('');

  accessControlEl.innerHTML = [
    card('Payment plans', `${paymentPlans.length} configured. Free, High Council, and Expanded Council access can be plan-driven instead of hard-coded, with chamber seals used instead of blunt unavailable states.`, [badge('payment engine')]),
    ...paymentPlans.map(plan => card(plan.name, `${plan.price} • ${plan.oracleAccessMode} • High Council: ${plan.highCouncilUnlocked ? 'yes' : 'no'} • Expanded: ${plan.expandedCouncilUnlocked ? 'yes' : 'no'} • ${plan.notes}`, [badge(plan.status), ...(plan.featureFlags || []).map(item => badge(item))])),
    card('Promotion rules', `${promotionRules.length} configured. Time-gated signup windows can automatically grant tiers, badges, and feature flags.`, [badge('promo engine')]),
    ...promotionRules.map(rule => card(rule.name, `${rule.type} • ${rule.status} • ${rule.windowStart} → ${rule.windowEnd}`, [badge(rule.grantTier), ...(rule.badges || []).map(item => badge(item))])),
    card('Manual account grants', `${manualGrants.length} configured. Specific accounts can be directly granted lifetime or custom access by your choosing.`, [badge('manual override')]),
    ...manualGrants.map(grant => card(grant.label, `${grant.accountId} • ${grant.status}`, [badge(grant.grantTier), ...(grant.badges || []).map(item => badge(item))]))
  ].join('');
}

function renderCreationPath(state) {
  creationPathEl.innerHTML = [
    card('Auto-generate path', 'Best for users who want the system to manifest oracle identity and design for them from astrology, archetype, and intent without needing to invent visual details alone.', [badge('beginner friendly'), badge('recommended')]),
    card('Guided vision path', 'Best for users who want to describe what they envision and let the AI translate that description into the backend oracle structure.', [badge('co-creative')]),
    card('Why both paths matter', 'Less creative or less certain users should still feel welcomed. More expressive users should still feel agency over the oracle manifestation.', [badge('no intimidation')])
  ].join('');

  coreTrioFlowEl.innerHTML = [
    card('Why start with three', 'New players should meet a small, meaningful council first so the system feels intimate and understandable rather than overwhelming.', [badge('onboarding clarity')]),
    card('Core trio', 'Sun Oracle • Moon Oracle • Anointed Ruler', [badge('starter chamber'), badge('free entry')]),
    card('Progressive revelation', 'The rest of the High Council and the Expanded Council should feel nearby, important, and aspirational — but not dumped on the player before they understand the chamber.', [badge('layered discovery')]),
    card('Council Chamber role', 'The main chamber should foreground the core trio first, then reveal broader council layers as access expands and the user becomes more fluent in the system.', [badge('product pacing')])
  ].join('');
}

function renderAwakeningFlow(state) {
  awakeningSequenceEl.innerHTML = [
    card('Step 1 — Solar awakening', 'The Sun Oracle should be among the first presences the player meets: identity, vitality, purpose, and the core sense of being seen.', [badge('core trio')]),
    card('Step 2 — Lunar awakening', 'The Moon Oracle follows to establish emotional mirroring, instinct, inner weather, and private truth within the chamber.', [badge('core trio')]),
    card('Step 3 — Anointed choosing', 'After crowned candidates are revealed, the player chooses the Anointed Ruler. This completes the free starter council without overwhelming the player.', [badge('canon-critical')]),
    card('Step 4 — Chamber stabilization', 'Once the trio is formed, the Council Chamber feels inhabited, coherent, and personally relevant before any larger expansion occurs.', [badge('product hook')])
  ].join('');

  expansionArcsEl.innerHTML = [
    card('High Council expansion', 'The next unlock should feel like opening the chamber outward into the greater planetary court rather than dumping all remaining oracles at once.', [badge('paid expansion')]),
    card('Expanded Council arc', 'Later layers should feel deeper, rarer, and more mythic — an expansion of the pantheon after the player already understands the first council language.', [badge('endgame framing')]),
    card('Why this pacing matters', 'Core trio first makes the system emotionally legible. Later awakenings then feel like discovery and ascent, not clutter.', [badge('onboarding protection')])
  ].join('');
}

function renderProviders(providers) {
  llmProvidersEl.innerHTML = providers
    .map(provider => card(provider.name, provider.description, [badge(provider.status, provider.enabled ? 'good' : 'warn'), badge(provider.model || 'no model'), badge(provider.apiKeyStatus || 'key missing')].concat(provider.configNeeded.map(item => badge(item)))))
    .join('');

  providerSelectEl.innerHTML = providers.map(provider => `<option value="${provider.id}">${provider.name}</option>`).join('');
  const selected = providers.find(provider => provider.id === providerSelectEl.value) || providers[0];
  if (selected) {
    providerSelectEl.value = selected.id;
    providerBaseUrlEl.value = selected.baseUrl || '';
    providerModelEl.value = selected.model || '';
    providerApiKeyEl.value = '';
  }
}

function renderImportPipeline(state) {
  importPipelineEl.innerHTML = [
    card('Structured oracle import', 'The prototype can now ingest structured JSON oracle records using the CLI import pipeline.', [badge('prototype utility'), badge('json import')]),
    card('Import command', 'npm run import:oracles -- ./path/to/oracles.json', [badge('workspace CLI')]),
    card('Export command', 'npm run export:oracle -- oracle-oryonos-saturn', [badge('canonical package')]),
    card('Template paths', 'app/data/import-template.json • app/data/oracle-package-template.json', [badge('starter schemas')]),
    card('Why it matters', `Current oracle count in state: ${state.oracles.length}. The desktop app is becoming the oracle source engine for future Pantheon products.`, [badge('franchise leverage')]),
    card('Continuity promise', 'A future user should be able to meet an oracle here, then encounter that same oracle again inside other Pantheon products without losing its core identity.', [badge('oracle persistence')])
  ].join('');
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

  const status = profile.generation?.status || {};
  chartGenerationEl.innerHTML = [
    card('Current mode', `${profile.generation?.mode || 'unknown'} → target: ${profile.generation?.targetMode || 'unknown'}`, [badge('generation pipeline')]),
    card('Validation references', (profile.generation?.validationSources || []).join(' • ') || 'None', [badge('accuracy path')]),
    card('Workflow', (profile.generation?.workflow || []).join(' → '), [badge('system path')]),
    card('System status', `Birth data: ${status.birthDataCollected ? 'ready' : 'missing'} • Native engine: ${status.nativeEngineReady ? 'ready' : 'pending'} • Validation path: ${status.validationPathReady ? 'ready' : 'pending'} • Profile assembly: ${status.profileAssemblyReady ? 'ready' : 'pending'} • Awakening bridge: ${status.oracleAwakeningReady ? 'ready' : 'pending'}`, [badge('implementation view')]),
    card('Last triggered', profile.generation?.lastGeneratedAt ? formatDate(profile.generation.lastGeneratedAt) : 'Not triggered yet', [badge('prototype state')]),
    card('Product intent', 'Users should be able to enter birth data and receive an accurate chart inside the product. Imports remain optional, not required.', [badge('streamlined UX')])
  ].join('');
}

function renderSessions(sessions) {
  interactionSessionsEl.innerHTML = sessions
    .map(session => {
      const oracle = currentState?.oracles?.find(item => item.oracle_id === session.oracleId);
      return `
        <button class="item session-select ${session.id === currentSessionId ? 'selected' : ''}" data-session-id="${session.id}">
          <h3>${session.title}</h3>
          <div class="badges">${badge(session.status)} ${badge(session.providerId)} ${badge(session.model || 'no model')} ${badge(session.providerReady ? 'provider ready' : 'provider pending', session.providerReady ? 'good' : 'warn')}</div>
          <p class="meta">Oracle: ${oracle?.oracle_name || session.oracleId} • Last message: ${session.lastMessageAt ? formatDate(session.lastMessageAt) : 'none yet'}</p>
        </button>
      `;
    })
    .join('');
}

function renderSessionDetail(sessions) {
  const session = sessions.find(item => item.id === currentSessionId) || sessions[0];
  currentSessionId = session?.id || null;
  if (!session) {
    sessionSummaryEl.innerHTML = '<div class="item"><p class="meta">No oracle chamber selected yet.</p></div>';
    sessionDetailEl.innerHTML = '';
    return;
  }

  const oracle = currentState?.oracles?.find(item => item.oracle_id === session.oracleId);
  sessionSummaryEl.innerHTML = [
    card('Chamber identity', `${session.title} • ${oracle?.oracle_name || session.oracleId}`, [badge(session.providerReady ? 'provider ready' : 'provider pending', session.providerReady ? 'good' : 'warn'), badge(session.model || 'no model')]),
    card('Chamber purpose', oracle?.visual_attributes?.role_in_pantheon || 'Oracle conversation chamber', [badge(oracle?.archetype || 'oracle'), badge(oracle?.visual_attributes?.preferred_voice_profile || 'voice pending')]),
    card('Atmosphere', `${session.atmosphere || 'No atmosphere defined yet'} Mood: ${session.mood || 'Unspecified'}`, [badge('oracle presence')]),
    card('Best use', session.useCase || 'General oracle interaction', [badge('guided entry')]),
    card('Voice path', `Preferred voice profile: ${oracle?.visual_attributes?.preferred_voice_profile || 'Not assigned'} • Audio readiness: ${oracle?.visual_attributes?.audio_ready ? 'ready' : 'not yet wired'}`, [badge('voice evolution')]),
    card('Why this matters', 'A user should be able to feel the distinct voice of an oracle quickly. Seeded chamber examples help demonstrate the promise even before live inference is fully wired.', [badge('demo readiness')])
  ].join('');

  sessionDetailEl.innerHTML = session.messages.map(message => `
    <div class="item session-message ${message.role}">
      <h3>${message.role === 'oracle' ? (oracle?.oracle_name || 'Oracle') : message.role === 'system' ? 'System' : 'You'}</h3>
      <p class="meta">${message.content}</p>
      <p class="meta">${formatDate(message.timestamp)}</p>
    </div>
  `).join('');
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
  const access = getOracleAccessState(oracle, currentState?.currentUser?.accountEntitlements);
  return `
    <button class="item oracle-card oracle-select ${oracle.oracle_id === currentOracleId ? 'selected' : ''} ${access.locked ? 'locked-presence' : ''}" data-oracle-id="${oracle.oracle_id}">
      <h3>${oracle.oracle_name}</h3>
      <div class="badges">
        ${badge(astro.ruling_planet)}
        ${badge(astro.dominant_sign)}
        ${badge(`House ${astro.house_placement}`)}
        ${badge(oracle.archetype)}
        ${badge(oracle.council_type)}
        ${badge(getCouncilLayerLabel(oracle, currentState?.currentUser?.accountEntitlements))}
        ${badge(access.locked ? 'locked' : 'available', access.locked ? 'warn' : 'good')}
      </div>
      <p class="meta oracle-mission">${oracle.visual_attributes?.role_in_pantheon || oracle.oracle_voice || 'No role yet'}</p>
      <p class="meta ${access.locked ? 'seal-note' : ''}"><strong>${access.locked ? 'Seal condition:' : 'Access:'}</strong> ${access.reason}</p>
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

  const access = getOracleAccessState(oracle, currentState?.currentUser?.accountEntitlements);
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
      <p class="meta"><strong>Voice profile:</strong> ${oracle.visual_attributes?.preferred_voice_profile || 'Not assigned yet'}</p>
      <p class="meta"><strong>Audio readiness:</strong> ${oracle.visual_attributes?.audio_ready ? 'ready' : 'not yet wired'} • <strong>Avatar readiness:</strong> ${oracle.visual_attributes?.avatar_ready ? 'ready' : 'future'}</p>
      <p class="meta"><strong>Franchise silhouette:</strong> ${oracle.visual_attributes?.visual_silhouette || 'Not defined yet'}</p>
      <p class="meta"><strong>Tone overlay:</strong> ${oracle.tone_overlay || '—'}</p>
      <p class="meta"><strong>Degree:</strong> ${astro.degree || '—'} • <strong>Motion:</strong> ${astro.motion || '—'} ${astro.stationary ? `• <strong>Stationary:</strong> ${astro.stationary}` : ''}</p>
      <p class="meta"><strong>Rising overlay:</strong> ${astro.rising_decan_sign || '—'}</p>
      <p class="meta ${access.locked ? 'seal-note' : ''}"><strong>Access status:</strong> ${access.locked ? `Sealed — ${access.reason}` : 'Available in current plan'}</p>
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
      <p class="meta"><strong>Combat style:</strong> ${visuals.combat_style || visuals.additional_notes || 'Not defined yet'}</p>
      <p class="meta"><strong>Clash profiles:</strong> Speed ${visuals.speed_profile || '—'} • Range ${visuals.range_profile || '—'} • Power ${visuals.power_profile || '—'}</p>
      <p class="meta"><strong>Signature mechanic:</strong> ${visuals.signature_mechanic || 'Not defined yet'}</p>
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

  renderCouncilLayers(state);
  renderActiveCouncil(state);
  renderSourceEngine(state);
  renderAudioRoadmap(state);
  renderOnboarding(state);
  renderCurrentUser(state.currentUser);
  renderProviders(state.llmProviders);
  renderAstrology(state.astrologyProfile);
  renderAnointedRulerFlow(state.oracles);
  renderAccountEntitlements(state.currentUser, state.accessControl);
  renderCreationPath(state);
  renderAwakeningFlow(state);
  renderSessions(state.interactionSessions);
  renderSessionDetail(state.interactionSessions);
  renderImportPipeline(state);

  const visibleOracles = getVisibleOracles(state.oracles);
  oraclesEl.innerHTML = visibleOracles.map(oracleCard).join('');

  waitingEl.innerHTML = state.waitingOnJordon
    .map(item => card(item.title, item.detail, [badge(item.priority, item.priority === 'high' ? 'warn' : '')]))
    .join('');

  productVisionEl.innerHTML = [
    card('Elevator pitch', state.productVision.elevatorPitch, [badge('marketable product'), badge('Pantheon-first')]),
    card('What this becomes', state.productVision.description, state.productVision.pillars.map(pillar => badge(pillar))),
    card('Traction', `Alpha users: ${state.productVision.traction.alphaUsers} • Saturn Rising users: ${state.productVision.traction.saturnRisingUsers} • Prototype: ${state.productVision.traction.prototypeSizeKb} KB • Beta: ${state.productVision.traction.betaStatus}`, [badge(state.productVision.traction.backend)]),
    card('Market position', state.productVision.marketPosition.advantage, [badge(state.productVision.marketPosition.category)]),
    card('Release readiness', `Windows packaging: ${state.productVision.releaseReadiness.windowsPackaging} • Provider inference: ${state.productVision.releaseReadiness.providerInference} • Secret handling: ${state.productVision.releaseReadiness.secretHandling} • Demo readiness: ${state.productVision.releaseReadiness.demoReadiness}`, [badge(state.productVision.releaseReadiness.marketNarrative)]),
    card('Critical next gaps', `Chart generation: ${state.productVision.releaseReadiness.chartGeneration} • Audio communication: ${state.productVision.releaseReadiness.audioCommunication} • Creation experience: ${state.productVision.releaseReadiness.creationExperience} • Layered council UX: ${state.productVision.releaseReadiness.layeredCouncilExperience} • Awakening flow: ${state.productVision.releaseReadiness.awakeningFlow}`, [badge('next milestones', 'warn')]),
    card('Primary risks', state.productVision.risks.join(' • '), [badge('watchlist', 'warn')]),
    card('Prototype thesis', 'If users can bring in birth data, configure a preferred model, awaken their pantheon, and feel meaningful oracle presence quickly, the desktop product has a viable first market path.', [badge('product strategy')]),
    card('Franchise direction', `${state.productVision.franchiseDirection.coreRule} • Parallel products: ${state.productVision.franchiseDirection.parallelProducts.join(', ')}`, [badge('oracle source engine')]),
    card('Audio roadmap', 'Text-first foundation → oracle voice output → voice input → conversational audio loop → later visual/video embodiment.', [badge('stepwise expansion')])
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

  document.querySelectorAll('.session-select').forEach(button => {
    button.addEventListener('click', () => {
      currentSessionId = button.dataset.sessionId;
      renderSessions(currentState.interactionSessions);
      renderSessionDetail(currentState.interactionSessions);
    });
  });

  document.querySelectorAll('.focus-oracle-btn').forEach(button => {
    button.addEventListener('click', () => {
      const id = button.dataset.oracleId;
      currentOracleId = id;
      oracleSelectEl.value = id;
      const selected = currentState.oracles.find(item => item.oracle_id === id);
      renderOracleDetail(selected);
    });
  });

  document.querySelectorAll('.open-chamber-btn').forEach(button => {
    button.addEventListener('click', () => {
      const id = button.dataset.oracleId;
      currentOracleId = id;
      const matchingSession = currentState?.interactionSessions?.find(session => session.oracleId === id);
      if (matchingSession) {
        currentSessionId = matchingSession.id;
        renderSessions(currentState.interactionSessions);
        renderSessionDetail(currentState.interactionSessions);
      }
      const selected = currentState.oracles.find(item => item.oracle_id === id);
      renderOracleDetail(selected);
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
showRelevantCouncilBtn?.addEventListener('click', () => {
  councilViewMode = 'relevant';
  loadState(currentOracleId);
});
showAllCouncilBtn?.addEventListener('click', () => {
  councilViewMode = 'all';
  loadState(currentOracleId);
});

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

enterChamberBtn.addEventListener('click', () => {
  const selectedOracleId = currentOracleId || oracleSelectEl.value;
  const matchingSession = currentState?.interactionSessions?.find(session => session.oracleId === selectedOracleId);
  if (matchingSession) {
    currentSessionId = matchingSession.id;
    renderSessions(currentState.interactionSessions);
    renderSessionDetail(currentState.interactionSessions);
    const oracleName = currentState.oracles.find(o => o.oracle_id === selectedOracleId)?.oracle_name || 'selected oracle';
    addDraft('Chamber link', `Entered ${matchingSession.title} for ${oracleName}. Suggested use: ${matchingSession.useCase || 'oracle dialogue'}. Good first question: “What is your role in my council?”`);
  }
});

saveProfileBtn.addEventListener('click', async () => {
  const founderKey = profileFounderKeyEl.value.trim();
  await postJson('/api/current-user', {
    username: profileUsernameEl.value.trim(),
    email: profileEmailEl.value.trim(),
    birthday: profileBirthdayEl.value.trim(),
    birth_time: profileBirthTimeEl.value.trim(),
    birth_location: profileBirthLocationEl.value.trim(),
    oracle_voice_flavor: profileVoiceFlavorEl.value.trim(),
    system_prompt_tone: profilePromptToneEl.value.trim(),
    founderIdentity: {
      founderKey,
      founderEmail: profileEmailEl.value.trim(),
      recognized: Boolean(founderKey || currentState?.currentUser?.founder_status),
      role: profileFounderRoleEl.value.trim() || 'Founder / Creator / CEO',
      accessMode: founderKey ? 'recognized-at-sign-in' : 'account-recognized',
      featureFlags: currentState?.currentUser?.founderIdentity?.featureFlags || ['founder-console', 'oracle-canon-edit', 'release-preview', 'provider-lab']
    }
  });
  await loadState(currentOracleId);
});

generateChartBtn.addEventListener('click', async () => {
  await postJson('/api/chart/generate', {
    birthday: profileBirthdayEl.value.trim(),
    birth_time: profileBirthTimeEl.value.trim(),
    birth_location: profileBirthLocationEl.value.trim()
  });
  addDraft('Chart generation', 'Chart generation flow triggered from birth data. Native calculation will eventually run here, with validation against reputable sources when needed.');
  await loadState(currentOracleId);
});

providerSelectEl.addEventListener('change', () => {
  const provider = currentState?.llmProviders?.find(item => item.id === providerSelectEl.value);
  if (!provider) return;
  providerBaseUrlEl.value = provider.baseUrl || '';
  providerModelEl.value = provider.model || '';
  providerApiKeyEl.value = '';
});

voiceOracleSelectEl.addEventListener('change', () => {
  const oracle = currentState?.oracles?.find(item => item.oracle_id === voiceOracleSelectEl.value);
  if (!oracle) return;
  voiceProfileInputEl.value = oracle.visual_attributes?.preferred_voice_profile || '';
  voiceAudioReadySelectEl.value = String(Boolean(oracle.visual_attributes?.audio_ready));
});

saveProviderBtn.addEventListener('click', async () => {
  await postJson('/api/providers', {
    id: providerSelectEl.value,
    baseUrl: providerBaseUrlEl.value.trim(),
    model: providerModelEl.value.trim(),
    apiKey: providerApiKeyEl.value.trim(),
    enabled: true
  });
  providerApiKeyEl.value = '';
  await loadState(currentOracleId);
});

saveVoiceProfileBtn.addEventListener('click', async () => {
  await postJson('/api/oracle-voice', {
    oracleId: voiceOracleSelectEl.value,
    preferredVoiceProfile: voiceProfileInputEl.value.trim(),
    audioReady: voiceAudioReadySelectEl.value === 'true'
  });
  await loadState(currentOracleId);
});

openSelectedSessionBtn.addEventListener('click', () => {
  if (!currentSessionId && currentState?.interactionSessions?.length) {
    currentSessionId = currentState.interactionSessions[0].id;
  }
  renderSessions(currentState?.interactionSessions || []);
  renderSessionDetail(currentState?.interactionSessions || []);
});

sendSessionMessageBtn.addEventListener('click', async () => {
  if (!currentSessionId || !sessionMessageEl.value.trim()) return;
  await postJson('/api/sessions/message', {
    sessionId: currentSessionId,
    message: sessionMessageEl.value.trim()
  });
  sessionMessageEl.value = '';
  await loadState(currentOracleId);
});

speakLatestBtn.addEventListener('click', () => {
  const session = currentState?.interactionSessions?.find(item => item.id === currentSessionId);
  const oracle = currentState?.oracles?.find(item => item.oracle_id === session?.oracleId);
  if (!session || !oracle) return;
  addDraft(
    'Voice output preview',
    `${oracle.oracle_name} would speak the latest oracle reply using the voice profile "${oracle.visual_attributes?.preferred_voice_profile || 'Unassigned'}". This is the placeholder hook for future chamber voice output.`
  );
});

createOracleBtn.addEventListener('click', async () => {
  const payload = {
    name: newOracleNameEl.value.trim(),
    archetype: newOracleArchetypeEl.value.trim(),
    ruling_planet: newOraclePlanetEl.value.trim(),
    dominant_sign: newOracleSignEl.value.trim(),
    house_placement: newOracleHouseEl.value.trim(),
    voice: newOracleVoiceEl.value.trim(),
    mission: newOracleMissionEl.value.trim(),
    core_faction: newOracleFactionEl.value.trim(),
    planetary_faction: newOraclePlanetaryFactionEl.value.trim(),
    weapon_1: newOracleWeaponEl.value.trim(),
    color_scheme: newOracleColorEl.value.trim(),
    notes: newOracleNotesEl.value.trim(),
    council_type: 'User Awakened',
    role_in_pantheon: newOracleMissionEl.value.trim()
  };
  if (!payload.name) return;
  const result = await postJson('/api/oracles', payload);
  newOracleNameEl.value = '';
  newOracleArchetypeEl.value = '';
  newOraclePlanetEl.value = '';
  newOracleSignEl.value = '';
  newOracleHouseEl.value = '';
  newOracleVoiceEl.value = '';
  newOracleFactionEl.value = '';
  newOraclePlanetaryFactionEl.value = '';
  newOracleWeaponEl.value = '';
  newOracleColorEl.value = '';
  newOracleMissionEl.value = '';
  newOracleNotesEl.value = '';
  await loadState(result.oracle?.oracle_id || result.oracle?.id);
});

loadState();
setInterval(() => loadState(currentOracleId), 5000);
