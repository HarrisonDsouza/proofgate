#!/usr/bin/env bash
# Push the harry branch and merge every open PR into main, safely.
# Run from the project root:  bash scripts/ship.sh        (DRY_RUN=1 bash scripts/ship.sh to test without pushing/merging)
#
# Steps: checks -> clean tree -> expected commit -> secret checks -> lint -> full test suite (+ the timing test alone)
#        -> push harry -> merge PR from harry -> for every other open PR: merge it onto the new main in a throwaway
#        worktree, run lint + the full suite there, merge only if green -> report.
# It never force-pushes, never uses --admin, never deletes branches, and never prints .env or key values.
set -euo pipefail

REPO="HarrisonDsouza/proofgate"
BRANCH="harry"
MUST_CONTAIN="116fef8"
FLAKY="tests/test_voice_routes.py::test_slow_speech_to_text_does_not_block_heartbeats"
SECRET_RE='(sk-ant-|sk-[A-Za-z0-9]{20,}|pa-[A-Za-z0-9_-]{30,}|lsv2_[A-Za-z0-9_]{20,}|mongodb\+srv://[^<" ]+:[^<" ]+@)'
DRY_RUN="${DRY_RUN:-0}"

ROOT="$(pwd)"
export PATH="$ROOT/.venv/bin:$PATH"
WORK="$(mktemp -d)"
REPORT="$WORK/report.txt"
trap 'git -C "$ROOT" worktree prune >/dev/null 2>&1 || true' EXIT

say()  { printf '\n== %s\n' "$*"; }
note() { printf '%s\n' "$*" | tee -a "$REPORT"; }
die()  { printf '\nSTOPPED: %s\n' "$*" >&2; [ -s "$REPORT" ] && { echo "--- report so far"; cat "$REPORT"; }; exit 1; }
run()  { if [ "$DRY_RUN" = 1 ]; then echo "[dry run] $*"; else "$@"; fi; }

# Run a command with the project's .env loaded by the Makefile (values are exported, never printed).
printf 'envrun:\n\t@$(CMD)\n' > "$WORK/env.mk"
with_env() { make -s -f "$ROOT/Makefile" -f "$WORK/env.mk" -C "$ROOT" envrun CMD="$*"; }

# Run the full suite in DIR; pass if green, or if the only failure is the known timing test and it passes alone.
suite() {
  local dir="$1" label="$2" out="$WORK/pytest-$2.txt"
  say "Full test suite on Atlas ($label), about 6 minutes"
  with_env "cd '$dir' && pytest -q -p no:cacheprovider 2>&1" > "$out" || true
  local summary failed
  summary="$(grep -E '[0-9]+ (passed|failed)' "$out" | tail -1)"
  failed="$(grep -E '^FAILED ' "$out" | awk '{print $2}' || true)"
  [ -n "$summary" ] || { tail -20 "$out"; die "test suite ($label) did not finish"; }
  note "Tests ($label): $summary"
  if [ -n "$failed" ]; then
    if [ "$failed" = "$FLAKY" ]; then
      note "  only failure is the known timing test; re-running it alone"
      with_env "cd '$dir' && pytest -q -p no:cacheprovider '$FLAKY' 2>&1" > "$WORK/flaky-$label.txt" || true
      grep -qE '1 passed' "$WORK/flaky-$label.txt" || die "timing test also fails alone ($label)"
      note "  timing test alone: passed"
    else
      echo "$failed"; die "tests failed ($label)"
    fi
  fi
  # the timing test alone, every time, as requested
  with_env "cd '$dir' && pytest -q -p no:cacheprovider '$FLAKY' 2>&1" > "$WORK/flaky2-$label.txt" || true
  grep -qE '1 passed' "$WORK/flaky2-$label.txt" || die "timing test fails when run alone ($label)"
  note "Timing test run alone ($label): passed"
}

# CI cannot be used if GitHub refuses to start jobs (account billing lock). Any other CI failure stops the merge.
ci_ok() {
  local pr="$1" bad=0
  while IFS=$'\t' read -r name state _dur link; do
    [ "$state" = "fail" ] || continue
    local job="${link##*/}"
    if gh api "repos/$REPO/check-runs/$job/annotations" -q '.[].message' 2>/dev/null | grep -qi "billing"; then
      note "  CI '$name' did not run: GitHub account billing lock (local tests used instead)"
    else
      note "  CI '$name' FAILED: $link"; bad=1
    fi
  done < <(gh pr checks "$pr" 2>/dev/null || true)
  return $bad
}

wait_mergeable() {
  local pr="$1" m
  for _ in $(seq 1 12); do
    m="$(gh pr view "$pr" --json mergeable -q .mergeable)"
    [ "$m" != "UNKNOWN" ] && { echo "$m"; return; }
    sleep 5
  done
  echo UNKNOWN
}

secret_check_diff() {  # scans added lines only; prints file names, never the matching text
  local hits
  hits="$(git -C "$ROOT" diff "$1" "$2" -- . ':!*.md' ':!.env.example' | grep -E '^\+' | grep -cE "$SECRET_RE" || true)"
  [ "$hits" = 0 ] || die "possible secret in the diff $1..$2 ($hits line(s)); not merging"
  git -C "$ROOT" diff --name-only "$1" "$2" | grep -qxE '\.env' && die ".env is in the diff $1..$2"
  return 0
}

say "1. Checks"
[ -f Makefile ] && [ -d pg ] || die "run this from the project root"
gh auth status >/dev/null 2>&1 || die "gh is not logged in (run: gh auth login)"
[ "$(git branch --show-current)" = "$BRANCH" ] || die "not on branch $BRANCH"
[ -z "$(git status --porcelain)" ] || { git status --short; die "working tree is not clean; commit or stash first"; }
git fetch -q origin
git merge-base --is-ancestor "$MUST_CONTAIN" HEAD || die "HEAD does not contain $MUST_CONTAIN"
git merge-base --is-ancestor origin/main HEAD || die "$BRANCH is behind main; merge main into $BRANCH first"
note "Branch $BRANCH at $(git rev-parse --short HEAD), contains $MUST_CONTAIN, up to date with main"

say "2. Secrets"
git ls-files --error-unmatch .env >/dev/null 2>&1 && die ".env is tracked by git"
make -s secret-scan
secret_check_diff origin/main HEAD
note "Secret checks: .env not tracked, secret-scan PASS, no key patterns in $BRANCH's diff"

say "3. Lint"
make -s lint
note "Lint: PASS"

suite "$ROOT" "$BRANCH"

say "4. Push $BRANCH"
run git push origin "$BRANCH"
note "Pushed $BRANCH at $(git rev-parse --short HEAD)"

say "5. Open PRs"
gh pr list --repo "$REPO" --state open --json number,title,headRefName,author,isDraft \
  -q '.[] | "#\(.number) [\(.headRefName)] \(.title) (by \(.author.login))\(if .isDraft then " DRAFT" else "" end)"' | tee -a "$REPORT"

merge_pr() {  # merge_pr <number> <expected head sha>
  local pr="$1" sha="$2"
  [ "$(wait_mergeable "$pr")" = "MERGEABLE" ] || die "PR #$pr is not mergeable on GitHub (conflicts?)"
  ci_ok "$pr" || die "PR #$pr has failing CI that is not the billing lock"
  run gh pr merge "$pr" --repo "$REPO" --merge --match-head-commit "$sha"
  note "Merged PR #$pr (head $sha)"
  git fetch -q origin
}

say "6. Merge the $BRANCH PR"
OWN="$(gh pr list --repo "$REPO" --state open --head "$BRANCH" --json number -q '.[0].number')"
[ -n "$OWN" ] || die "no open PR from $BRANCH"
merge_pr "$OWN" "$(git rev-parse HEAD)"

say "7. Every other open PR: test on top of the new main, then merge"
for pr in $(gh pr list --repo "$REPO" --state open --json number,isDraft -q '.[] | select(.isDraft | not) | .number'); do
  head="$(gh pr view "$pr" --json headRefOid -q .headRefOid)"
  git fetch -q origin "pull/$pr/head:refs/ship/pr-$pr" || die "cannot fetch PR #$pr"
  wt="$WORK/pr-$pr"
  git worktree add -q --detach "$wt" origin/main
  if ! git -C "$wt" -c user.name="ship" -c user.email="ship@localhost" merge -q --no-edit "refs/ship/pr-$pr" >/dev/null 2>&1; then
    git -C "$wt" merge --abort || true
    git worktree remove --force "$wt"
    note "PR #$pr: CONFLICTS with main, left open for manual resolution"; continue
  fi
  secret_check_diff origin/main "refs/ship/pr-$pr"
  (cd "$wt" && ruff check pg eval seed tests data >/dev/null) || { git worktree remove --force "$wt"; die "PR #$pr fails lint on top of main"; }
  suite "$wt" "pr-$pr-on-main"
  git worktree remove --force "$wt"
  merge_pr "$pr" "$head"
done

say "8. Result"
left="$(gh pr list --repo "$REPO" --state open --json number -q 'length')"
note "Open PRs left: $left"
note "main is now $(git rev-parse --short origin/main)"
echo; echo "===== REPORT ====="; cat "$REPORT"
[ "$DRY_RUN" = 1 ] && echo "(dry run: nothing was pushed or merged)"
exit 0
