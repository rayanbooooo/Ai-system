# Architecture

## Why two execution environments

This repo is built and version-controlled from a cloud Claude Code session.
That session runs in an ephemeral container: it cannot host a long-lived
process, and its own scheduled automation (Routines) can't fire more than
once an hour. Watching 1-minute futures structure needs something that runs
continuously, so the system is split:

```
                       ┌─────────────────────────────┐
                       │   Your PC (market hours)     │
                       │                               │
  Tradovate API  ────▶ │  scanner/main.py (Python)     │
                       │   - pulls 1H/15m/1m bars       │
                       │   - runs the 6-step state       │
                       │     machine (structure/)         │
                       │   - on Step 6: fires Telegram      │
                       │     alert + writes vault note       │
                       └───────────────┬─────────────────────┘
                                       │ writes
                                       ▼
                       ┌─────────────────────────────┐
                       │   vault/ (Obsidian, in repo)  │
                       │   Accounts, Journal, Signals,  │
                       │   Payouts, Rules, Dashboard      │
                       └───────────────┬─────────────────┘
                                       │ git commit/push
                                       │ (Obsidian Git plugin,
                                       │  auto-sync ~5-10 min)
                                       ▼
                       ┌─────────────────────────────┐
                       │   This repo (cloud)            │
                       │                                  │
                       │  Claude Code Routines (hourly+)   │
                       │   - daily rule digest               │
                       │   - payout eligibility check          │
                       │   - weekly journal rollup                │
                       │   - daily journal prompt                  │
                       │  read/write vault notes                     │
                       └─────────────────────────────────────────────┘
```

**Telegram alerts bypass git entirely** — the scanner sends them directly
and immediately when Step 6 fires. Git/vault sync is only for the
slower-cadence dashboard/journal/digest side; never rely on it for
time-sensitive alerting.

## Components

- **`scanner/`** — deterministic, non-LLM Python service. Structure
  detection is a mechanical rule/state machine (see
  `docs/AZAREL_STRATEGY.md`), not an LLM call per candle: it needs to be
  fast, deterministic, and cheap to run continuously.
- **`config/`** — your real accounts, Apex's rule numbers (placeholders you
  must verify), instrument specs and scan thresholds.
- **`vault/`** — the Obsidian vault. Also the hand-off point between the
  scanner (writes) and the cloud Routines (read + write).
- **`routines/`** — the prompt text for each Claude Code Routine. These are
  specs, not yet registered as live scheduled triggers — see
  `docs/OPEN_QUESTIONS.md` for why, and register them (via `create_trigger`
  or the `/loop` skill) once `config/accounts.yaml` and `config/rules.yaml`
  hold real data.
- **`scanner/annotator/`** — a pluggable interface for optionally drawing
  the AZAREL step-stair lines/pivots on a live TradingView Desktop chart via
  a local CDP bridge. Only a no-op implementation exists today; see
  `docs/OPEN_QUESTIONS.md` before building the real one.

## Hosting

The scanner is meant to run on your own PC, kept on during market hours
(your choice, made so that Phase 5 chart-drawing stays possible later,
since CDP control of TradingView Desktop only works on the same machine
that's running it). It can equally run as `python -m scanner.main` under a
process supervisor (e.g. `pm2`, `supervisord`, or a simple `launchd`/Task
Scheduler entry) so it restarts if it crashes.
