import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();
const importPath = process.argv[2];
if (!importPath) {
  console.error('Usage: node scripts/import-oracles.mjs <path-to-json>');
  process.exit(1);
}

const statePath = join(root, 'app', 'data', 'state.json');
const state = JSON.parse(readFileSync(statePath, 'utf8'));
const payload = JSON.parse(readFileSync(importPath, 'utf8'));

if (payload.currentUser) {
  state.currentUser = { ...state.currentUser, ...payload.currentUser };
}
if (payload.astrologyProfile) {
  state.astrologyProfile = { ...state.astrologyProfile, ...payload.astrologyProfile };
}
if (Array.isArray(payload.oracles)) {
  for (const oracle of payload.oracles) {
    if (!state.oracles.find(item => item.oracle_id === oracle.oracle_id)) {
      state.oracles.push(oracle);
      state.sessions.push({
        id: `session-${oracle.oracle_id}`,
        oracleId: oracle.oracle_id,
        providerId: state.providers[0]?.id || 'default-provider',
        model: state.providers[0]?.model || '',
        providerReady: state.providers[0]?.ready || false,
        messages: [
          { role: 'oracle', text: `${oracle.oracle_name} was imported into the chamber.` }
        ]
      });
    }
  }
}

writeFileSync(statePath, JSON.stringify(state, null, 2));
console.log('Imported into state:', importPath);