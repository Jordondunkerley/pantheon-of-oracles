import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();
const statePath = join(root, 'app', 'data', 'state.json');
const outDir = join(root, 'exports', 'oracle-packages');
const oracleId = process.argv[2];

if (!oracleId) {
  console.error('Usage: node scripts/export-oracle-package.mjs <oracle_id>');
  process.exit(1);
}

const state = JSON.parse(readFileSync(statePath, 'utf8'));
const oracle = state.oracles.find(item => item.oracle_id === oracleId);
if (!oracle) {
  console.error(`Oracle not found: ${oracleId}`);
  process.exit(1);
}

const pkg = {
  canonical_id: oracle.oracle_id,
  identity: {
    oracle_name: oracle.oracle_name,
    title: oracle.title || '',
    archetype: oracle.archetype || '',
    voice: oracle.voice || '',
    mission: oracle.mission || '',
    notes: oracle.notes || ''
  },
  astrology: {
    ruling_planet: oracle.ruling_planet || '',
    dominant_sign: oracle.dominant_sign || '',
    house_placement: oracle.house_placement || '',
    aspects: oracle.aspects || [],
    transit_modifiers: oracle.transit_modifiers || []
  },
  faction: {
    core_faction: oracle.faction || '',
    planetary_faction: oracle.planetary_faction || '',
    role: oracle.role || ''
  },
  visual: {
    color_scheme: oracle.color_scheme || '',
    weapon: oracle.weapon || '',
    silhouette: oracle.silhouette || '',
    spirit_animal: oracle.spirit_animal || ''
  },
  franchise_traits: {
    combat_style: oracle.combat_style || '',
    guidance_style: oracle.guidance_style || '',
    relationship_mode: oracle.relationship_mode || '',
    export_version: '0.1.0'
  },
  future_product_hooks: {
    clash: {
      role_hint: oracle.role || '',
      combat_style: oracle.combat_style || ''
    },
    mobile: {
      guidance_style: oracle.guidance_style || ''
    },
    retro2d: {
      silhouette: oracle.silhouette || '',
      weapon: oracle.weapon || ''
    }
  }
};

mkdirSync(outDir, { recursive: true });
const outPath = join(outDir, `${oracle.oracle_id}.json`);
writeFileSync(outPath, JSON.stringify(pkg, null, 2));
console.log(outPath);