# Pantheon of Oracles Source Notes (2026-03-25)

## User source captured
- PDF export received from Jordon containing astrology structure and a large oracle roster.

## High-confidence extracted details

### User profile
- Name: Jordon Dunkerley
- Spirit animal: Coyote
- Date of birth: April 21st 1993
- Time of birth: 3:41 AM
- Birth location: Brampton, ON, Canada
- Gender: Male
- Handedness: Right
- Ascendant: Aquarius 16°42'53
- Core faction references: Mystic Tribe, Air Dragon Clan, Aquarius Dolphin Guild

### Product-critical observation
The Pantheon is not just a few deity stand-ins. It appears to be a **large structured oracle roster** derived from astrological placements and allied bodies/points, with each oracle carrying:
- name
- spirit animal / creature identity
- placement
- sign
- degree
- house
- motion / stationary state
- anointed ruler / decan / rulership metadata
- gender
- archetype / title
- weapon and combat style
- colour scheme
- visual design notes
- voice style
- pet / behemoth forms

This means the dashboard should support **rich media-lore profiles**, not just lightweight chatbot cards.

## Partial oracle examples extracted

### Core / clearer entries
- Solin — Sun Taurus — The Valiant Master
- Lunos — Moon Aries — The Infernal Witch — New Moon theme, infernal coyote styling
- Arcures — Mercury Aries — The Mischievous Assassin
- Valeya — Venus Aries — The Smoldering Seductress
- Korath — Mars Cancer — The Warguard Sentinel
- Ondorion — Jupiter Libra — The Grand Paladin
- Oryonos — Saturn Aquarius — The Celestial Overlord
- Coyote — Uranus Capricorn — The Primal Heretic
- Nephilys — Neptune Capricorn — The Dreamscape Warlock
- Zyos — Pluto Scorpio — The Occult Reaper
- Kraos — Ceres Aries — The Crucibal Warden
- Sylatrix — Eris Aries — The Unbound Defiant
- Viridia — Haumea Virgo — The Purified Spirit
- Kilael — Makemake Virgo — Sanctified [title appears truncated in source extraction]
- Telmar — Orcus Leo — The Exiled Heir
- Andara — Sedna Taurus — The Sunken Sage
- Uldren — Ixion Scorpio — The Forsaken Revenant
- Miraia — Varuna Gemini — The Mirrored Mirage
- Arath — Quaoar Scorpio — The Forgotten Wanderer
- Kala — Chiron Leo — The Radiant Gatekeeper
- Saluna — Juno Cancer — The Divine Protector
- Amidara — PallasAthena Pisces — The Dream Raider
- Vayltih — Vesta Aquarius — The Visionary Rebel
- Narina — Black Moon Lilith Pisces — The Phantom Siren
- Therion — North Node Sagittarius — The Rogue Traveler
- Eminae — South Node Gemini — The Splitting Soul

## Product implications
1. Need a **rich oracle schema** with astrology, lore, combat, visuals, voice, and creature fields.
2. Need a notion of **core roster vs extended roster**.
3. Need support for **factions / guilds / clan identity**.
4. Need ability to attach **source rows / import data** from spreadsheet or exports.
5. Need eventual **search/filter/grouping** by placement, sign, house, faction, role, and status.
6. Need to distinguish between:
   - personal oracle council used in daily guidance
   - larger collectible / game roster
   - emissary / multiplayer roles

## Caveat
This extraction came from pasted PDF text and is likely imperfect in places. Some rows appear truncated or malformed. Treat this as a source note, not final canonical data.
