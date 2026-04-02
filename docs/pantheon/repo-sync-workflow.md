# Pantheon Repo Sync Workflow

## Goal
Make daily GitHub checkpoints routine and reliable so Pantheon progress is not lost again.

## Standing rules
1. By the end of each day, sync meaningful Pantheon progress to the GitHub repo.
2. Only sync states that are coherent, downloadable, and founder-testable for the current stage.
3. Avoid leaving the repo in a broken halfway state if it can be stabilized first.

## Minimum daily checkpoint checklist
- review local changes
- confirm app structure still coherent
- confirm package metadata and docs are up to date
- ensure the repo snapshot is founder-testable relative to current reconstruction stage
- create/update a checkpoint manifest when the change set is large
- create a clear commit message describing the real product progress
- push to the Pantheon repo
- explicitly report back to Jordon that the repo has been updated and is testable

## Preferred commit style
- `Restore chamber hierarchy and founder flow`
- `Add oracle registry and oracle comms surfaces`
- `Align package metadata and desktop wrapper with live repo`
- `Stabilize founder-testable recovery checkpoint`

## Operational note
Repo sync should be treated as part of finishing the day, not an optional extra after the work is done.