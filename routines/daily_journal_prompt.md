# Routine: daily-journal-prompt

**Status:** spec only, not yet registered - see `docs/OPEN_QUESTIONS.md`.

**Cron:** `0 21 * * 1-5` (~5pm US/Eastern on weekdays, assuming EDT/UTC-4 -
shift to `0 22 * * 1-5` during EST/winter).

**Reads:** `vault/Journal/Daily/_Daily_Template.md`.

**Writes:** seeds today's `vault/Journal/Daily/YYYY-MM-DD.md` if it
doesn't already exist (the daily-rule-digest Routine, or the user, may
have already created it earlier in the day - don't overwrite).

## Prompt

```
Pull the latest changes in this repo. If
vault/Journal/Daily/<today's date, YYYY-MM-DD>.md does not already exist,
create it from vault/Journal/Daily/_Daily_Template.md with today's date
filled in. If it already exists, do nothing - never overwrite an existing
daily note.

If you created a new note, commit and push it with a message like "Seed
daily journal for <date>". If it already existed, make no changes and do
not commit.
```
