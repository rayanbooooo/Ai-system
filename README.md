# Ai-system

A personal trading-assistant system for passing and managing Apex Trader
Funding evaluation/PA accounts (MNQ, MGC futures on Tradovate/TradingView),
built around an Obsidian vault.

**What this is:**

- A rule-based (non-AI, deterministic) chart-structure **scanner** that
  watches for "A+ setups" per a specific 6-step method and sends **Telegram
  alerts for you to execute manually**. It never places trades automatically.
- A **rules & risk tracker**: per-account drawdown/loss-limit/trading-day
  state, tracked in Obsidian.
- A **payout tracker**: eligibility windows and request history.
- An **Obsidian vault** (`vault/`) as the dashboard/journal, including every
  Telegram alert logged as a searchable note.

**What this is not:** an auto-trading bot. Nothing in this repo places,
modifies, or closes an order on your Tradovate account.

## Repo layout

- `scanner/` — the Python scanner (runs on your own machine, see below)
- `config/` — your accounts, Apex rule numbers, instrument specs
- `vault/` — the Obsidian vault (open this folder directly in Obsidian)
- `routines/` — spec text for the Claude Code Routines that do daily/weekly
  Obsidian housekeeping (rule digests, payout reminders, journal rollups)
- `docs/` — setup guides and the strategy spec

## Why the scanner doesn't run in this cloud repo

This repository is built and version-controlled from a cloud Claude Code
session, which runs in an ephemeral container and cannot host a persistent
real-time process, and whose own scheduling can't fire more than once an
hour — far too coarse to watch 1-minute futures structure. So:

- The **scanner** (`scanner/`) is meant to run on **your own PC**, kept on
  during market hours (see `docs/ARCHITECTURE.md`).
- The **Claude Code Routines** (`routines/`) handle the slower-cadence
  Obsidian work (daily digest, payout check, weekly rollup) by reading and
  writing vault notes on an hourly-or-slower schedule.
- Git (recommended: the free **Obsidian Git** community plugin, auto-sync
  every 5-10 min) is what connects the two — the scanner commits/pushes
  vault updates, the Routines pull the latest before acting.

## Getting started

1. Read `docs/ARCHITECTURE.md` for the full picture.
2. Fill in `config/accounts.yaml` with your real Apex account(s).
3. Verify and fill in `config/rules.yaml` with Apex's **current official**
   rule numbers — every value ships as a placeholder marked `EXAMPLE/VERIFY`
   and must not be trusted as-is.
4. Follow `docs/TRADOVATE_SETUP.md` and `docs/TELEGRAM_SETUP.md` to get API
   credentials, then copy `.env.example` to `.env` and fill it in.
5. Open `vault/` in Obsidian (install the free **Dataview** community
   plugin so `Dashboard.md` and templates render).
6. Run the scanner in replay mode first (`python -m scanner.main
   --replay-htf scanner/tests/fixtures/mnq_long_htf.csv --replay-ltf
   scanner/tests/fixtures/mnq_long_ltf.csv --instrument MNQ`) and read
   `docs/OPEN_QUESTIONS.md` — the structure-detection thresholds need
   calibration against your own historical chart examples before you
   trust a live alert.

See `docs/AZAREL_STRATEGY.md` for the exact 6-step setup logic this scanner
implements.
