# Open Questions / Things To Resolve Before Trusting This Live

Tracked here instead of silently assumed, so nothing gets treated as
authoritative that hasn't actually been confirmed.

## Strategy calibration (highest priority)

The 6-step checklist's prose (see `docs/AZAREL_STRATEGY.md`) doesn't pin
down every numeric threshold:

- Fractal lookback window for confirming a swing high/low.
- Minimum displacement size that counts as a "strong candle body closure"
  for Step 5.
- Zone tolerance for "price returned into the Step 2 order block" (Step 4).
- What exactly invalidates an in-progress setup (zone fully violated before
  Step 5, or a timeout on the Step 6 retest never arriving).

Current values in `config/instruments.yaml` are placeholders. **Before any
live Telegram alert is trusted:** supply 5-10 historical chart examples
(screenshots or bar data + your own annotation of where each of the 6 steps
occurred) so the thresholds can be tuned until `scanner/main.py --replay`
output matches your manual reads. Then run a 1-2 week shadow period with
Telegram alerts disabled (vault/console logging only) before enabling real
alerts.

## Tradovate API access

- Confirm your Tradovate plan actually includes API market-data access, or
  whether a separate market-data subscription is required.
- Confirm demo vs. live endpoint for each Apex account — Apex accounts are
  sometimes routed through Tradovate's demo environment even though real
  funding/rules are involved.
- If Tradovate API access stalls or is cost-prohibitive, the fallback is a
  dedicated read-only futures data vendor (e.g. Databento, Polygon.io) for
  OHLC bars only — trading still happens manually on Tradovate regardless
  of where bar data comes from. Not built yet; only pursue if needed.

## Apex rule numbers

Every value in `config/rules.yaml` is a placeholder marked EXAMPLE/VERIFY.
Apex's actual current rules (drawdown type/amount, daily loss limit, min
trading days, consistency rule, payout cadence and split) must be checked
against Apex Trader Funding's own current published terms and kept up to
date — they are known to change over time and by promotion/account tier.

## Routines not yet registered

`routines/*.md` are written as specs but intentionally **not** registered
as live scheduled triggers yet, since `config/accounts.yaml` only has a
placeholder account. Registering hourly+ cron jobs that summarize empty
data isn't useful and would just be noise. Register them (see each file's
header for the recommended cron expression) once real account data is in
place.

## Known simplifications in the current scanner code

- Once STEP 4 arms the LTF tracker, `HTFTracker` stops evaluating further
  HTF bars for that setup (see the `step == 4` branch in
  `scanner/structure/htf_tracker.py::observe_bar`) - so if price fully
  invalidates the zone at the HTF level while the LTF tracker is still
  watching for STEPS 5-6, only the LTF tracker's own timeout
  (`timeout_bars_ltf`) will eventually disarm it, not an HTF-level
  invalidation check. Worth adding an explicit HTF-side check if false
  signals show up during calibration.
- The HTF tracker only runs on one timeframe (`instruments.yaml`'s last
  `htf` entry, currently 15m) even though the spec names "15m/1H" - 1H is
  not currently used as a secondary confirmation. Decide whether STEP 1
  should require both timeframes to agree, or stay 15m-only.
- `SolidifiedPointTracker` has a strict ordering contract: for a given
  bar, `observe_bar` must run before `observe_swing_point` for any swing
  point that bar just confirmed (see its docstring and the regression
  test `test_a_belated_deeper_swing_point_does_not_erase_an_earlier_sweep`
  in `scanner/tests/test_solidified_point.py`). `state_machine.py` already
  follows this - keep it that way in any future caller.

## DST drift

Claude Code Routine cron expressions are UTC-only and fixed; US market
hours shift with DST twice a year, so any Routine schedule anchored to a
specific ET time will drift by an hour for part of the year unless manually
adjusted (`update_trigger`) around DST changes in March/November.

## Vault sync freshness

The cloud Routines only see whatever the last Obsidian Git sync pushed.
If a digest looks stale, first check the sync interval/last-sync time
before assuming the Routine or scanner is broken.

## Phase 5: live chart annotation via CDP

The user described a local MCP server (`tv_health_check`, `tv_launch`,
`draw_shape`, `draw_list`, `draw_remove_one`, `draw_clear`) that draws on a
live TradingView Desktop chart via Chrome DevTools Protocol remote
debugging. This cloud repo session searched its available tools/connectors
and found no such server — expected, since CDP control of a desktop app
only works from a process on the same machine as that app.

Before building `scanner/annotator/cdp_annotator.py` for real:

1. In your **local** Claude Code session (not this cloud one), confirm
   `tv_health_check` actually resolves and successfully connects to a
   running TradingView Desktop instance.
2. Decide whether the scanner itself should speak CDP directly (e.g. via a
   Python websocket client — CDP is just JSON-RPC over a websocket, so this
   doesn't strictly require going through an MCP server or an LLM in the
   loop), or whether draw commands should be queued to a file/socket that
   your local Claude Code session polls and executes via its MCP tools.
   Direct CDP from the scanner is simpler and doesn't depend on an LLM
   session being open; recommended if (1) checks out.

Until both are confirmed, `scanner/annotator/noop_annotator.py` is used by
default — it logs what it would have drawn and does nothing live.
