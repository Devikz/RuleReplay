# RuleReplay engineering instructions

Build the three-way comparison of legacy Java, updated Python, and an approved,
versioned financial-policy oracle. Follow phases 0–7 in PROJECT_STATUS.md.

- Python 3.12, FastAPI/Pydantic; React/TypeScript/Vite/Tailwind.
- The independent deterministic oracle is the authority. AI generates hypotheses,
  never authoritative expected values or verdicts.
- Use synthetic data. Monetary outputs are integer cents; dates are ISO calendar dates.
- Never print, commit, or send credentials to the browser or execution sandbox.
- Preserve existing `.env` values. Paid Meta and Modal calls default to disabled and
  require explicit human approval before enabling. Never push without approval.
- Never execute submitted code on the host. Only repository-owned, reviewed fixtures
  may run in local tests; arbitrary source runs exclusively in Modal Sandboxes.
- Label offline generation and local fixture simulation honestly. Do not present
  offline outcomes as measured Muse Wonder or Modal results.
- Keep dependency/disk usage small; no model weights or local Docker images.
- Run relevant tests after each phase; update PROJECT_STATUS.md with actual evidence,
  limitations, and outstanding live checks. Do not fabricate benchmark results.
- Commands: `uv run pytest`, `uv run ruff check .`, `npm --prefix frontend test`,
  `npm --prefix frontend run build`. Local dev: `python3.12 scripts/dev.py`.

## Senior hardening maintenance

- Follow the actual boundaries and decision table in `docs/HIGH_LEVEL_DESIGN.md` and
  `docs/POLICY_MODEL.md`. Oracle/classifier must not import providers, fixtures or model output.
- Keep `release.outcome` evidence-derived. A green simulator run is UNVERIFIED; incomplete
  generation or execution evidence requires REVIEW. The legacy summary field is not approval.
- Every correctness/security fix needs a focused regression test. Preserve original suites.
- Use one backend process. Do not automatically retry an ACCEPTED durable operation claim;
  inspect provider/evidence state before risking repeat billing.
- Run `uv run bandit -r backend -q`, `uv run python scripts/security_audit.py`, and
  `npm --prefix frontend run test:e2e` alongside original checks. Feed outages are UNVERIFIED,
  not clean security results. Browser tests use installed Chrome and disposable offline servers.
- Benchmark tuning against known defects must be disclosed as in-sample. Recompute saved
  benchmark data whenever its generator/source changes; never edit scores by hand.
- Do not commit, push or publish without explicit user approval.
