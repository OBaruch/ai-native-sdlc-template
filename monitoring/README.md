# monitoring/ — closing the loop

```
metrics store ──► detect.py (deterministic) ──► tier
                                                 ├─ 1σ  log only
                                                 ├─ 2σ  the selected agent diagnoses read-only ─► intent.md PR ─► triage
                                                 └─ 3σ  the selected agent proposes: PR into review gate
                                                        and/or a pre-approved runbook
```

| File | Purpose |
|------|---------|
| `bands.yaml` | Metrics, sources, owners, response tiers and the runbook allowlist (version-controlled policy) |
| `detect.py` | Rolling baseline + Western Electric rules. No model. Unit-tested in `tests/` |
| `sources/` | Small adapters that print a metric series as JSON (GitHub CLI, Prometheus) |
| `respond.sh` | Turns 2σ/3σ findings into PRs (intent or report) and triggers allowed runbooks |
| `runbooks/` | Pre-approved procedures the loop may trigger |
| `reports/` | Process-metric reports (created on demand) |

## Adopting it
1. Pick **one** metric with a stable baseline; set its `source.command` and `owner` in `bands.yaml`.
2. Run `python3 monitoring/detect.py --metric <name>` locally and check the series looks right.
3. Enable the workflow (`SDLC_ENABLED=true` repo variable) — it runs every 30 minutes.
4. Triage the `maintain-loop` PRs: fix now, schedule, or dismiss. Tune the bands from dismissals.
5. When a fix ships, add an eval for the incident (`evals/`).

## Measure
- Leading: time from breach (detect log / workflow run) to the intent PR.
- Lagging: share of `maintain-loop` PRs that end in merged fixes; repeat incidents of the same class.

The selected adapter comes from SDLC_AGENT_ADAPTER. Tier configuration uses portable `mode`
(read-only by default), not native allowed-tool strings. Changing a mode requires policy review
and an adapter/sandbox that enforces it. See `.agents/README.md` for boundary limits.

Response runs use disposable clones and preserve the source checkout. Read-only mutations
are rejected before publication. Runbook routes/modes come from version-controlled bands.yaml,
not model output or finding-supplied permissions. Existing open triage PRs are skipped; pushes
never force-overwrite another branch. Workspace-write proposals must pass make check.
