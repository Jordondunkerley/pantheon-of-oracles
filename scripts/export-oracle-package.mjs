import fs from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const statePath = path.join(root, 'app', 'data', 'state.json');
const outputDir = path.join(root, 'exports', 'oracle-packages');
const oracleId = process.argv[2];

if (!oracleId) {
  console.error('Usage: node scripts/export-oracle-package.mjs <oracle_id>');
  process.exit(1);
}

const state = JSON.parse(await fs.readFile(statePath, 'utf8'));
const oracle = state.oracles.find(item => item.oracle_id === oracleId);
if (!oracle) {
  console.error(`Oracle not found: ${oracleId}`);
  process.exit(1);
}

await fs.mkdir(outputDir, { recursive: true });

const visual = oracle.visual_attributes?.visual_description || {};
const weapons = oracle.visual_attributes?.weapons || {};
const pkg = {
  package_version: '0.1.0',
  oracle_id: oracle.oracle_id,
  oracle_name: oracle.oracle_name,
  source_product: 'Pantheon of Oracles Desktop Prototype',
  canonical: true,
  astrology_profile: oracle.astrology_profile,
  identity: {
    archetype: oracle.archetype,
    oracle_type: oracle.oracle_type,
    oracle_voice: oracle.oracle_voice,
    tone_overlay: oracle.tone_overlay,
    role_in_pantheon: oracle.visual_attributes?.role_in_pantheon || '',
    preferred_voice_profile: oracle.visual_attributes?.preferred_voice_profile || '',
    audio_ready: Boolean(oracle.visual_attributes?.audio_ready),
    avatar_ready: Boolean(oracle.visual_attributes?.avatar_ready)
  },
  franchise_traits: {
    weapon_signature: weapons.weapon_1 || '',
    combat_style: oracle.visual_attributes?.combat_style || oracle.visual_attributes?.additional_notes || '',
    visual_silhouette: oracle.visual_attributes?.visual_silhouette || `${visual.head || ''} ${visual.torso || ''}`.trim(),
    color_scheme: visual.color_scheme || '',
    spirit_identity: oracle.visual_attributes?.spirit_identity || oracle.pet_name || oracle.behemoth_name || ''
  },
  faction_affiliation: oracle.faction_affiliation,
  visual_attributes: {
    head: visual.head || '',
    torso: visual.torso || '',
    arms: visual.arms || '',
    legs: visual.legs || '',
    aura: visual.aura || '',
    ambient_flavor: visual.ambient_flavor || '',
    visual_style_notes: visual.visual_style_notes || ''
  },
  future_hooks: {
    supports_clash: true,
    supports_mobile: true,
    supports_story_modes: true
  },
  game_interpretation: {
    clash_archetype: oracle.archetype || '',
    speed_profile: oracle.visual_attributes?.speed_profile || '',
    range_profile: oracle.visual_attributes?.range_profile || '',
    power_profile: oracle.visual_attributes?.power_profile || '',
    signature_mechanic: oracle.visual_attributes?.signature_mechanic || '',
    stance_fantasy: oracle.visual_attributes?.stance_fantasy || ''
  }
};

const outPath = path.join(outputDir, `${oracle.oracle_id}.json`);
await fs.writeFile(outPath, JSON.stringify(pkg, null, 2) + '\n', 'utf8');
console.log(`Exported oracle package to ${outPath}`);
