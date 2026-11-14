# Workflow: git and pull requests

**One rule above all:** `main` must always run. Nobody pushes to `main` directly. Work lands through pull requests (PRs).

## Branches

| Branch | Who | Folders you may change |
|---|---|---|
| `main` | everyone, via PRs only | - |
| `harry` | Harry | `pg/db.py`, `pg/target.py`, `pg/agent.py`, `pg/rules.py`, `seed/`, `data/`, `eval/` (except `test_conflict.py`), `ui/` (except `ui/src/voice/`), `Makefile`, `README.md`, `docs/PREREGISTRATION.md` |
| `sukhman` | Sukhman | `pg/review.py`, `pg/checks.py`, `pg/gate.py`, `pg/detector.py`, `pg/cusum.py`, `pg/riskcontrol.py`, `pg/stats.py`, `eval/test_conflict.py`, `docs/DATA.md` |
| `neil` | Neil | `pg/voice.py`, `ui/src/voice/`, tracing lines in `pg/observability.py` and `pg/agent.py` (agree with Harry first) |

Staying in your own folders means almost no merge conflicts. Everyone may add their own test files in `tests/`. To change a shared file (`pg/main.py` routes, `pg/config.py`, `.env.example`, `requirements*.txt`, `project-docs/handoffs.md`, an API shape from PRD §8), tell the other people **before** you push.

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

When something works, `make ci` passes, and you have its proof command (a curl, a test, or `make <target>`):
```bash
gh pr create --base main --head <your-name> --title "Gate transaction G1-G8" --body "How to check: <command>"
```
Or open it on github.com: the repo page shows "Compare & pull request".

- Put the **proof command** in the description, so whoever merges can run it.
- Small PRs, often: at least one per hour, and always before a checkpoint (13:15, 13:45, 14:30, 16:00).
- **No untested pushes after 15:00.** Run `make ci` (ruff, pytest, secret scan) before every PR. GitHub Actions runs the same checks once the account billing lock is cleared.
- **Every PR is reviewed by the tech lead** (Harry's Claude Code session). There is no automatic reviewer and no API key. When you open a PR, message Harry with the PR number.
  - The review runs `make ci` on your branch, a code review, and a security review if the PR touches the gate, the target or grants.
  - It checks: no secrets; the CLAUDE.md invariants; folder ownership; bugs on the demo path; and that the PR has a proof command.
  - It posts one PR comment that starts with "Verdict: OK to merge", "Verdict: merge after fixes" or "Verdict: do not merge".
  - Every PR and its verdict are logged in [project-docs/WORKLOG.md](project-docs/WORKLOG.md).
- **Don't merge your own PR**: the tech lead merges after an OK verdict. If Harry is unreachable for 15 minutes and `make ci` passes, you may merge, and say so in the PR.
- **After 16:00, bug-fix PRs only.** Anything else gets "do not merge".

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
| 13:15 | Smoke, setup and seed on the sandbox; fallback UI loads; `make bypass` PASS |
| 13:45 | Core demo works (bulk 50 → 0; honest review executes + read-back; forged dwell → 0; bypass → 403; `make test-conflict` PASS). Tag `core-ok` |
| 14:30 | `docs/PREREGISTRATION.md` merged before the held-out eval run |
| 15:30 | Fallback burst video recorded |
| 16:00 | **Feature freeze**: bug-fix PRs only |
| 16:45 | Submitted on Cerebral Valley |
