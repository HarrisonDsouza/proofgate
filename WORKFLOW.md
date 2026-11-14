# Workflow: git and pull requests

**One rule above all:** `main` must always run. Nobody pushes to `main` directly. Work lands through pull requests (PRs).

## Branches

| Branch | Who | Folders you may change |
|---|---|---|
| `main` | everyone, via PRs only | - |
| `harry` | Harry | `py/` (except `py/voice/`), `ui/` (except `ui/src/app/voice/`), `Makefile`, `README.md`, `docs/` |
| `sukhman` | Sukhman | `gate/` |
| `neil` | Neil | `py/voice/`, `ui/src/app/voice/`, `@traceable` lines in `py/agent/` (agree with Harry first) |

Staying in your own folders means almost no merge conflicts. To change a shared file (`.env.example`, `project-docs/handoffs.md`, an API shape from PRD §8), tell the other person **before** you push.

## 1. Clone once

```bash
git clone https://github.com/HarrisonDsouza/proofgate.git
cd proofgate
git checkout <your-name>        # harry, sukhman or neil
```
Then do the README "Sandbox setup" steps 1-3 (tools and `.env`).

## 2. Work and commit often

```bash
git status                      # .env must NOT be listed
git add <files>
git commit -m "Gate: add G5 dwell check"   # say what changed
git push
```
Commit every small working step. It is your undo button.

## 3. Open a pull request into main

When something works and has its proof command (a curl, a test, or `make <target>`):
```bash
gh pr create --base main --head <your-name> --title "Gate transaction G1-G8" --body "How to check: <command>"
```
Or open it on github.com: the repo page shows "Compare & pull request".

- Put the **proof command** in the description, so whoever merges can run it.
- Small PRs, often: at least one per hour, and always before a checkpoint (12:40, 13:45, 14:45, 15:30).
- Merge it yourself once the check passes (no review is required, to keep us fast), or ask a teammate to look first if it touches a shared file.

## 4. Sync with main (do it after every merge and before every PR)

```bash
git fetch origin
git merge origin/main           # bring teammates' work into your branch
# fix any conflicts, then:
git push
```
If a conflict touches someone else's folder, stop and ask them. Don't guess.

## 5. Handoffs

- When your piece is ready for someone else, update its row in [project-docs/handoffs.md](project-docs/handoffs.md) to `ready`, with the check command, and tell them.
- They mark it `accepted` once the check passes on their machine.

## Never

- Commit `.env`, keys or connection strings. If it happens, tell Harry at once: the key must be rotated, and deleting the file is not enough.
- Force-push to `main`, or rewrite history on a shared branch.
- Commit code you didn't write today.

## Timeline

| Time | What |
|---|---|
| 12:40 | Smoke test passes; data in Atlas |
| 13:45 | Core demo works (bulk 50 → 0; honest review executes; bypass → 403). Tag `core-ok` |
| 14:15 | `docs/preregistration.md` merged before any eval run |
| 15:30 | **Feature freeze**: bug-fix PRs only |
| 16:45 | Submitted on Cerebral Valley |
