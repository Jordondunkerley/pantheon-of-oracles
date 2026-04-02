# Pantheon Working Rules

## Daily repo sync rule
By the end of each day, updated Pantheon work should be saved back to the GitHub repo.

## Repo must stay testable
Whenever the repo is updated, it should be left in a state where Jordon can download the repo and test the current product state at any time.

### Intent
- avoid losing progress again
- keep reconstruction and live repo aligned
- treat repo sync as routine hygiene, not an exceptional task
- ensure the repo is a reliable founder-testable snapshot, not a broken halfway checkpoint

### Operating rule
- even if Jordon does not explicitly request it that day, the working expectation is: commit/push updated Pantheon progress daily when meaningful changes exist
- only sync states that are coherent, runnable, and founder-testable relative to the current reconstruction stage
- if a day ends with partial work, finish or stabilize the branch state before pushing so the repo remains usable as a download-and-test source
- whenever a repo update is actually completed, explicitly tell Jordon that the repo has been updated and is testable
- if automation/cron is later added, use it to support this habit rather than replace judgment

### Current caution
Git identity and reliable repo-write flow still need to be fully restored in the active workspace session before this can be executed automatically from here.