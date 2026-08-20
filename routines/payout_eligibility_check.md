# Routine: payout-eligibility-check

**Status:** spec only, not yet registered - see `docs/OPEN_QUESTIONS.md`.

**Cron:** `0 14 * * *` (~10am US/Eastern daily, assuming EDT/UTC-4 - shift
to `0 15 * * *` during EST/winter).

**Reads:** `vault/Accounts/*.md` (phase = `pa`), `vault/Payouts/*.md`
history, `config/rules.yaml#payout_rules`.

**Writes:** creates/updates `vault/Payouts/<account>-<period>.md`
(from `vault/Payouts/_Payout_Template.md`), flips `eligible: true` when a
window opens.

## Prompt

```
Pull the latest changes in this repo. For every account note under
vault/Accounts/*.md with phase: pa and status: active, check
config/rules.yaml#payout_rules (min_days_since_account_start,
min_days_between_payouts, min_trading_days_for_first_payout) against that
account's start_date, days_traded, and its payout history in
vault/Payouts/*.md (filter by account_id).

If the account has crossed into a new eligible payout window and there is
no existing vault/Payouts/<account_id>-<window>.md note for it, create one
from vault/Payouts/_Payout_Template.md with eligible: true and the
computed window_start/window_end. If a note already exists for the
current window, update its eligible field if it changed; never overwrite
a note whose status is anything other than not_requested (leave requested/
approved/paid/denied notes alone).

Commit and push any changes with a message like "Payout eligibility check
for <date>". Note in the commit body (or skip the commit entirely) if no
accounts had eligibility changes today. Remember every rule number here
comes from config/rules.yaml, which may be out of date - do not treat an
eligibility flag as certain if that file's last_verified looks stale.
```
