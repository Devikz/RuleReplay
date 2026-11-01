# Hardening and milestone change manifest

The original hardening-pass inventory below lists 67 repository files. The final
offline checkpoint reconciles it with all 98 changed/untracked milestone paths;
the additional 31 paths are listed separately below. These are scope inventories,
not reconstructed commit history or claims about individual authorship.

The checkout already contained uncommitted/untracked hackathon work at the start. This is a
pass-specific inventory, not a claim that every file shown by `git status` was newly created here.
No commit, push, history rewrite, existing report rewrite or `.env` edit was performed.

Generated ignored diagnostics (`coverage.xml`, frontend build/test output and `.local/security`)
are not source changes. Temporary Mermaid dependencies were used only for validation and removed afterward.

## Project configuration and CI

- `.gitignore`
- `.env.example`
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `README.md`
- `pyproject.toml`
- `uv.lock`
- `.github/workflows/ci.yml`
- `.github/dependabot.yml`

## Backend

- `backend/rulereplay/api.py`
- `backend/rulereplay/benchmark.py`
- `backend/rulereplay/classify.py`
- `backend/rulereplay/config.py`
- `backend/rulereplay/contracts.py`
- `backend/rulereplay/domain.py`
- `backend/rulereplay/evidence.py`
- `backend/rulereplay/execution.py`
- `backend/rulereplay/generation.py`
- `backend/rulereplay/integrity.py`
- `backend/rulereplay/lifecycle.py`
- `backend/rulereplay/main.py`
- `backend/rulereplay/operations.py`
- `backend/rulereplay/oracle.py`
- `backend/rulereplay/sandbox_runner.py`
- `backend/rulereplay/security.py`
- `backend/rulereplay/storage.py`
- `backend/rulereplay/verification.py`

## Frontend

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/vite.config.ts`
- `frontend/playwright.config.ts`
- `frontend/e2e/workflow.spec.ts`
- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/api.ts`
- `frontend/src/types.ts`

## Scripts

- `scripts/check_secrets.py`
- `scripts/security_audit.py`
- `scripts/e2e_server.py`

## Tests

- `tests/test_execution.py`
- `tests/test_architecture.py`
- `tests/test_hardening_evidence.py`
- `tests/test_hardening_security.py`
- `tests/test_planning_integration.py`
- `tests/test_policy_properties.py`
- `tests/test_reliability.py`
- `tests/test_security_audit.py`

## Measured benchmark artifacts

- `benchmarks/REPORT.md`
- `benchmarks/results.json`

## Engineering documentation

- `docs/ARCHITECTURE.md`
- `docs/ARCHITECTURE_REVIEW.md`
- `docs/HIGH_LEVEL_DESIGN.md`
- `docs/THREAT_MODEL.md`
- `docs/TEST_STRATEGY.md`
- `docs/RELIABILITY.md`
- `docs/POLICY_MODEL.md`
- `docs/EVALUATION.md`
- `docs/SECURITY.md`
- `docs/OPERATIONS.md`
- `docs/HARDENING_CHANGELOG.md`
- `docs/adr/001-modular-monolith.md`
- `docs/adr/002-independent-oracle.md`
- `docs/adr/003-meta-planning.md`
- `docs/adr/004-modal-isolation.md`
- `docs/adr/005-policy-provenance.md`
- `docs/adr/006-local-json.md`
- `docs/adr/007-offline-live.md`

## Additional milestone files — reconciled 2026-10-29

These 31 files are required parts of the broader uncommitted prototype. They were
outside the original hardening-pass list; omission from that list did not mean
that they should be excluded from the eventual milestone commit.

- `.npmrc`
- `.python-version`
- `backend/rulereplay/__init__.py`
- `backend/rulereplay/fixtures.py`
- `backend/rulereplay/minimize.py`
- `backend/rulereplay/policies.py`
- `backend/rulereplay/simulator.py`
- `data/policies.json`
- `docs/ATTRIBUTION.md`
- `docs/DEMO.md`
- `docs/RESEARCH.md`
- `fixtures/legacy/LegacyLoan.java`
- `fixtures/updated/corrected.py`
- `fixtures/updated/loan.py`
- `frontend/index.html`
- `frontend/src/main.tsx`
- `frontend/src/styles.css`
- `frontend/src/test-setup.ts`
- `frontend/src/vite-env.d.ts`
- `frontend/tsconfig.json`
- `scripts/dev.py`
- `scripts/setup.py`
- `tests/conftest.py`
- `tests/test_api.py`
- `tests/test_benchmark.py`
- `tests/test_config.py`
- `tests/test_engine.py`
- `tests/test_evidence.py`
- `tests/test_generation.py`
- `tests/test_sandbox_harness.py`
- `tests/test_trusted_fixtures.py`

## Publication review and disposition

Reviewed the complete 98-path working-tree inventory, including source/test boundaries,
synthetic fixtures and policy data, scripts/configuration, documentation claims, and
machine-checked lockfiles and benchmark artifacts. All 98 paths belong in the proposed
milestone; the unchanged tracked `LICENSE` is also required. No file should be staged
or committed until the user approves. This review is not a claim of live validation.

- **Retain source and tests:** all backend/frontend modules, fixed Java/Python fixtures,
  synthetic policies, original and added tests, offline browser harness and setup/dev scripts.
  Oracle/classifier independence and host-execution limits remain covered by regression tests.
- **Retain reproducibility artifacts:** `uv.lock` (77 packages), frontend lockfile (190
  dependency entries), and both benchmark files. Lockfile URLs use only public PyPI/Python
  package hosting and npm registries, with no embedded credentials. The saved benchmark
  was regenerated by the offline evaluator; scores were not edited manually.
- **Retain documentation/configuration:** all 21 documents under `docs/`, README, status,
  engineering instructions, Python/Node settings, empty `.env.example`, CI and Dependabot.
  Earlier test counts and 9/10 results remain labeled historical evidence; the current
  checkpoint and demo state the rerun 10/10 and its known-defect, in-sample tuning.
- **Exclude private/local output:** `.env`, `.local/` reports/operation receipts/audit output,
  `.venv/`, `frontend/node_modules/`, `.uv-cache/`, Python bytecode, `.pytest_cache/`,
  `.ruff_cache/`, `.hypothesis/`, `.coverage`, `coverage.xml`, `frontend/dist/`,
  `frontend/tsconfig.tsbuildinfo`, browser test results and Playwright reports. Existing
  ignore rules cover them. They were not removed or added to the milestone inventory.
- **Secret/data checks:** repository secret scanner covers all publishable files and built
  browser assets. Root `.env` is ignored, untracked, nonsymlinked and mode 0600; credentials
  are absent and both paid gates are false. The full publishable file set has no binary,
  symlink, vendored/local dependency, merge-marker or trailing-whitespace issue. Policy,
  fixture, test and benchmark data are synthetic; no customer dataset was found.
- **Git state:** `main` has one existing commit; only `.gitignore`, README and LICENSE are
  tracked. The milestone is two modified tracked files plus 96 untracked files, with no
  staged changes, deletions or merge conflicts. `git fsck --no-reflogs` reports two dangling
  trees, no corruption; retain them without pruning or inventing historical commits.
  Public GitHub CI remains unrun. The public repository will be incomplete until an
  explicitly approved commit includes all 98 paths, followed by a separately approved push.

The final fixes update history projection and shared verdict presentation, their API/UI/browser
regressions, formatting coverage, demo/README claims, benchmark outputs and this reconciliation.
No contribution dates, Git author dates or historical scores were fabricated or backdated.

## Milestone safeguarding and commit plan — 2026-11-01

Rechecked all **98 changed/untracked paths** against the two exact inventories above:
67 original hardening paths plus 31 broader milestone paths, with no missing or extra path.
The unchanged tracked LICENSE is the 99th publishable file. All 98 changed paths belong
in the proposed milestone; no generated/local-only path needs removal from that inventory.

| Source-control group | Changed paths | Disposition |
| --- | --- | --- |
| Root configuration, README, status and instructions | 9 | Include |
| CI and Dependabot | 2 | Include |
| Backend Python package | 23 | Include |
| Benchmark report and measured JSON | 2 | Include; generated reproducibility evidence, deliberately versioned |
| Synthetic policy data | 1 | Include |
| Documentation, including seven ADRs | 21 | Include |
| Reviewed Java/Python fixtures | 3 | Include |
| Frontend source, tests, configuration and lockfile | 15 | Include |
| Setup, dev, secret/audit and offline browser scripts | 5 | Include |
| Backend tests and fixtures | 17 | Include |
| **Total** | **98** | **Exact allowlist above** |

Fresh publication checks found no known local credential or configured secret-pattern match,
binary/symlink, conflict marker, trailing whitespace, vendored dependency directory or oversized
file. Before these planning updates the publishable set was 717,764 bytes; largest files were
`uv.lock` (146,440 bytes) and the frontend lockfile (104,064 bytes). The 77 Python packages and
190 npm dependency entries resolve through public PyPI/Python hosting and npm, without URL
credentials. Retain both locks and both benchmark artifacts; do not hand-edit measured scores.
All policy/test/fixture/benchmark inputs remain synthetic. Review fingerprints and diagnostics
are local-only under ignored `.local/review/`; they are not part of the allowlist.

Local disk use is approximately 107 MB `.venv`, 215 MB frontend dependencies, 108 MB uv cache
and 292 KB frontend build output. These directories remain ignored, as do `.env`, `.local`,
coverage, bytecode, test reports and other caches listed above. No weights, images or installed
packages belong in the commit. `.env` remains ignored/untracked, nonsymlinked, mode 0600 and
unchanged. The example's three credential assignments are empty; its other values are public
configuration/defaults, not credentials.

The existing MIT license is byte-for-byte identical to HEAD, including its original copyright
notice. The source review found no conflicting proprietary notice, copied third-party license
block or inappropriate new license assertion. Existing attribution remains; package license
metadata is retained in the lockfiles. Installed dependency license files stay with their
packages. This is a source publication review, not a completed redistribution-license audit
of a future packaged binary. No authorship or contribution date was invented or backdated.

### Execution sequence after explicit staging/commit approval

1. Recheck the worktree against the **98 exact paths** in this document and the latest local
   fingerprints; stop if any extra path, content change or pre-existing staged change appears.
   Preserve the unchanged LICENSE. Do not stage directories recursively or use `git add .`.
2. Stage only that allowlist using a NUL-delimited temporary pathspec file and
   `git add --pathspec-from-file=<temporary-allowlist> --pathspec-file-nul`.
   Build the allowlist from the 98 standalone path bullets above; verify set/count first.
3. Inspect `git diff --cached --stat`, `git diff --cached --check` and the complete staged diff.
   Compare staged file contents with the reviewed worktree and scan those exact staged bytes
   for secrets. Confirm no `.env` or excluded output is staged and exactly 98 paths are staged.
   If content changes after review, re-review and run checks relevant to that change.
4. Create one milestone commit with the message below and the existing configured Git identity
   and actual commit date. Do not amend, synthesize earlier commits or override author dates.
5. Verify the commit's path list and clean index. Keep the commit local. A push or publication
   requires a separate explicit approval; hosted CI has not run yet.

Recommended commit message:

```text
feat: establish policy-backed RuleReplay verification platform
```

Proposed body: establish the Java/Python/approved-policy comparison, deterministic oracle and
classifier, paid-gated Meta/Modal adapters, immutable evidence/replay, release advisories,
conservative operation controls, frontend, regression/security/browser tests and disclosed
offline benchmark. Offline readiness is complete; live provider validation remains unverified.

Current state remains `main`, one existing commit, two modified tracked files and 96 untracked
files, with no staged changes or merge conflicts. The two dangling Git trees remain unpruned;
`git fsck --no-reflogs` reports no corruption. A local commit is the pending safeguard; no
commit, push, publication, provider account change or billable operation was performed here.
