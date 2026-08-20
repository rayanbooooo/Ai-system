# Routine: weekly-journal-rollup

**Status:** spec only, not yet registered - see `docs/OPEN_QUESTIONS.md`.

**Cron:** `0 14 * * 0` (~10am US/Eastern on Sunday, assuming EDT/UTC-4 -
shift to `0 15 * * 0` during EST/winter).

**Reads:** the past 7 days of `vault/Journal/Daily/*.md` and
`vault/Signals/*.md`.

**Writes:** `vault/Journal/Weekly/YYYY-Www.md` (from
`vault/Journal/Weekly/_Weekly_Template.md`).

## Prompt

```
Pull the latest changes in this repo. Read every vault/Journal/Daily/*.md
note dated within the last 7 days, and every vault/Signals/*.md note
triggered in that same window.

Create (or update if it already exists, from
vault/Journal/Weekly/_Weekly_Template.md) this week's
vault/Journal/Weekly/<YYYY-Www>.md note. Fill in:
- "Summary": a short narrative of the week - how many setups fired, how
  many were executed, rough win/loss split if outcome fields are filled in.
- "What Worked / What Didn't": pull from the daily notes' "Lessons"
  sections and rule-check boxes.
- "Focus For Next Week": 2-3 concrete suggestions based on patterns you
  see (e.g. a rule getting checked "no" repeatedly, or a recurring theme
  in the lessons).

Leave the Dataview query blocks in the template as-is - do not replace
them with static text. Commit and push with a message like "Weekly
journal rollup for <week>".
```
