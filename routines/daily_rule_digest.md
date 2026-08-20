# Routine: daily-rule-digest

**Status:** spec only, not yet registered - see `docs/OPEN_QUESTIONS.md`
("Routines not yet registered"). Register once `config/accounts.yaml` and
`config/rules.yaml` hold real data.

**Cron:** `0 13 * * 1-5` (~9am US/Eastern on weekdays, assuming EDT/UTC-4 -
shift to `0 14 * * 1-5` during EST/winter; see docs/OPEN_QUESTIONS.md on
DST drift).

**Reads:** `vault/Accounts/*.md` frontmatter, `config/rules.yaml`.

**Writes:** appends a "Risk Digest" section to today's
`vault/Journal/Daily/YYYY-MM-DD.md` (creating the note from
`vault/Journal/Daily/_Daily_Template.md` first if it doesn't exist yet).

## Prompt (use as the Routine's `prompt` when registering via `create_trigger`)

```
Pull the latest changes in this repo. For every note under
vault/Accounts/*.md, read its frontmatter (account_id, phase, status,
max_drawdown, current_drawdown_used, daily_loss_limit,
daily_loss_used_today, days_traded, min_trading_days). Cross-check each
account's rules_ref against config/rules.yaml to make sure the numbers in
the note haven't drifted from the source of truth.

For today's date, open (creating from vault/Journal/Daily/_Daily_Template.md
if it doesn't exist yet) vault/Journal/Daily/<YYYY-MM-DD>.md and replace the
content under the "## Risk Digest" heading with a short per-account summary:
drawdown used vs. max (as a percentage), daily loss used vs. limit,
trading days completed vs. required, and a one-line flag for any account
above 80% of its drawdown or daily loss limit. Do not modify any other
section of the note.

Commit and push the change with a message like "Daily rule digest for
<date>". If any account's rules_ref points at a rule_sets key that no
longer exists in config/rules.yaml, or any rule value looks stale (e.g.
last_verified is empty or clearly old), flag that explicitly in the digest
instead of silently guessing.
```
