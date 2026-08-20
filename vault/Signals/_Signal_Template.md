---
type: signal
instrument: MNQ
direction: long
step_chain: [1, 2, 3, 4, 5, 6]
entry: 0.0
stop_loss: 0.0
take_profit: 0.0
triggered_at: 2026-08-20T00:00:00-04:00
accounts_notified: []
outcome: pending
executed: false
---

# {{instrument}} {{direction}} — {{triggered_at}}

Auto-written by `scanner/logging/vault_writer.py` whenever the state
machine fires a Step 6 entry and sends the matching Telegram alert. One
note per alert — this is the searchable signal history.

## Structure Chain

- Step 1 (HTF BOS):
- Step 2 (Order Block):
- Step 3 (Solidified Target / TP anchor):
- Step 4 (Zone Retracement):
- Step 5 (1m Displacement):
- Step 6 (Retest Entry):

## Outcome

- [ ] Executed
- Result:
- Notes:
