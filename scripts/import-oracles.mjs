import fs from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const statePath = path.join(root, 'app', 'data', 'state.json');
const inputPath = process.argv[2];

if (!inputPath) {
  console.error('Usage: node scripts/import-oracles.mjs <json-file>');
  process.exit(1);
}

const state = JSON.parse(await fs.readFile(statePath, 'utf8'));
const imports = JSON.parse(await fs.readFile(path.resolve(root, inputPath), 'utf8'));
const rows = Array.isArray(imports) ? imports : [imports];

const imported = rows.map((row, index) => ({
  oracle_id: row.oracle_id || `oracle-import-${Date.now()}-${index}`,
  oracle_name: row.oracle_name || 'Imported Oracle',
  archetype: row.archetype || 'Unformed Oracle',
  oracle_type: row.oracle_type || 'Playable',
  astrology_profile: {
    ruling_planet: row.ruling_planet || '',
    dominant_sign: row.dominant_sign || '',
    house_placement: row.house_placement || '',
    motion: row.motion || 'Direct',
    stationary: row.stationary || '',
    shadow: row.shadow || '',
    degree: row.degree || '',
    degree_mark: row.degree_mark || '',
    decan: {
      method: row.decan_method || 'Modern',
      decan_ruler: row.decan_ruler || '',
      decan_ruler_sign: row.decan_ruler_sign || '',
      flavor: row.decan_flavor || 'Full'
    },
    rising_sign: row.rising_sign || state.astrologyProfile?.angles?.Ascendant?.sign || '',
    rising_decan_sign: row.rising_decan_sign || ''
  },
  faction_affiliation: {
    core_faction: row.core_faction || state.currentUser?.faction_alignment?.core_faction || '',
    planetary_faction: row.planetary_faction || row.ruling_planet || '',
    tribe: row.tribe || '',
    guild: row.guild || state.currentUser?.faction_alignment?.guild || ''
  },
  hardcore_status: true,
  level: row.level || 0,
  tier: row.tier || 'Tier 1',
  ascended_rank: row.ascended_rank || 0,
  oracle_form: row.oracle_form || 'Base',
  council_type: row.council_type || 'Imported',
  descendant_relationship_state: row.descendant_relationship_state || 'Dormant',
  oracle_locked: false,
  oracle_voice: row.voice || '',
  tone_overlay: row.tone_overlay || row.role_in_pantheon || '',
  oracle_metadata_last_updated: new Date().toISOString(),
  anointed_ruler: Boolean(row.anointed_ruler),
  modern_ruler: Boolean(row.modern_ruler),
  traditional_ruler: Boolean(row.traditional_ruler),
  dominant_ruler: Boolean(row.dominant_ruler),
  solar_ruler: Boolean(row.solar_ruler),
  has_shapeshift: Boolean(row.has_shapeshift),
  shapeshift_description: row.shapeshift_description || '',
  has_pet: Boolean(row.has_pet),
  pet_name: row.pet_name || '',
  pet_description: row.pet_description || '',
  has_apprentice: Boolean(row.has_apprentice),
  apprentice_name: row.apprentice_name || '',
  apprentice_description: row.apprentice_description || '',
  has_disciple: Boolean(row.has_disciple),
  disciple_name: row.disciple_name || '',
  disciple_description: row.disciple_description || '',
  has_legion: Boolean(row.has_legion),
  legion_name: row.legion_name || '',
  legion_description: row.legion_description || '',
  has_legion_captain: Boolean(row.has_legion_captain),
  legion_captain_name: row.legion_captain_name || '',
  legion_captain_description: row.legion_captain_description || '',
  has_behemoth: Boolean(row.has_behemoth),
  behemoth_name: row.behemoth_name || '',
  behemoth_description: row.behemoth_description || '',
  has_behemoth_fusion: Boolean(row.has_behemoth_fusion),
  behemoth_fusion_name: row.behemoth_fusion_name || '',
  behemoth_fusion_crown: Boolean(row.behemoth_fusion_crown),
  behemoth_fusion_aura: Boolean(row.behemoth_fusion_aura),
  behemoth_fusion_description: row.behemoth_fusion_description || '',
  visual_attributes: {
    visual_description: {
      head: row.head || '',
      torso: row.torso || '',
      arms: row.arms || '',
      legs: row.legs || '',
      aura: row.aura || '',
      ambient_flavor: row.ambient_flavor || '',
      visual_style_notes: row.visual_style_notes || '',
      color_scheme: row.color_scheme || ''
    },
    weapons: {
      weapon_1: row.weapon_1 || '',
      weapon_2: row.weapon_2 || ''
    },
    oracle_avatar_url: row.oracle_avatar_url || '',
    voice_style: row.voice_style || row.voice || '',
    role_in_pantheon: row.role_in_pantheon || '',
    additional_notes: row.additional_notes || ''
  }
}));

state.oracles = [...imported, ...state.oracles];
state.activity.unshift({
  id: `activity-${Date.now()}`,
  type: 'oracle_import',
  message: `Imported ${imported.length} oracle profile(s) from ${path.basename(inputPath)}.`,
  timestamp: new Date().toISOString()
});
state.meta.updatedAt = new Date().toISOString();

await fs.writeFile(statePath, JSON.stringify(state, null, 2) + '\n', 'utf8');
console.log(`Imported ${imported.length} oracle(s).`);
