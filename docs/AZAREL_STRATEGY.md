# AZAREL Strategy — The 6-Step Checklist

This is the exact setup-detection logic implemented by `scanner/structure/`.
It is reproduced verbatim as the living spec: if the code and this document
ever disagree, this document (and the user's clarification) wins, and the
code should be fixed to match — not the other way around.

```
[ ] STEP 1: HTF Break of Structure (New Range)
    - Condition: Price breaks out of a higher-timeframe (15m/1H) Solidified Point.
    - Identification: A point is ONLY solidified if structure broke in BOTH directions
      (swept a low then broke above a high, or swept a high then broke below a low).
      The first break after a new range is a continuation break confirming the target.
    - Action: Identify the breakout leg and new expansion range.

[ ] STEP 2: The Last Opposite Push (Order Block)
    - Condition: Locate the exact last opposite candle/wick that caused the Step 1 breakout.
    - Identification: The last push down before a bullish breakout, or the last push up
      before a bearish breakout.
    - Action: Mark the level as a standing point of reference for the retracement.

[ ] STEP 3: Solidified Target High / Low
    - Condition: The Step 1 expansion takes out its target high/low, turns around, and
      breaks back below/above a solidified point.
    - Identification: This peak (for longs) or trough (for shorts) becomes the Step 3
      Solidified Target.
    - Action: Anchor this level as the ultimate Take Profit target for Step 6.

[ ] STEP 4: Zone Retracement (Macro Shift)
    - Condition: Price pulls back into the Step 2 Order Block level and creates a 3rd
      Solidified Point shift inside this zone.
    - Identification: Confirms higher-timeframe alignment and validates the hot zone.
    - Action: Prepare to drop to lower timeframes for micro execution.

[ ] STEP 5: 1-Minute Micro Displacement Shift
    - Condition: On the 1-minute chart inside the Step 4 hot zone, price executes a
      strong candle body closure breaking local swing structure (BOS/CHoCH).
    - Identification: Must show energetic displacement, leaving behind a 1m Last
      Opposite Push.
    - Action: Confirm the local directional shift.

[ ] STEP 6: Retest Entry & Target Execution
    - Condition: Price retraces back to touch the 1m Last Opposite Push identified in
      Step 5.
    - Entry: Limit/Market order on the retest of the 1m Last Opposite Push.
    - Stop Loss: Placed strictly beyond the 1m Solidified Point anchor.
    - Take Profit: Targeted directly at the Step 3 Solidified High/Low level.
```

## Visual marking rules ("AZAREL style")

These govern the optional Phase 5 chart annotator (`scanner/annotator/`),
not yet wired to anything live — see `docs/OPEN_QUESTIONS.md`.

1. **Step-stair horizontal line segments (no infinite rays):** draw clean
   horizontal segments extending rightwards from each Solidified High or
   Low. Terminate the segment at the exact candle where price breaks or
   sweeps that level. Connect successive ranges left-to-right in a
   continuous "step-stair" sequence.
2. **Pivot point markers (circles):** a small circular dot at every
   Solidified High (swing top) and Solidified Low (swing bottom).
3. **Minimalist number tags, no boxes/paragraphs:** label key structural
   levels using only standalone numbers ("1"–"6") next to the exact pivot
   or line segment. No shaded background boxes, no descriptive text.
4. **Persistence:** never erase or delete prior historical line segments or
   numbered pivots. Keep all past HTF (1H/15m) and LTF (1m) Solidified
   Points visible sequentially left-to-right.

## Implementation notes / where the spec is intentionally underspecified

The prose above does not pin down every numeric threshold. These are
implemented as configurable parameters (`config/instruments.yaml`) rather
than invented constants, and must be calibrated — see
`docs/OPEN_QUESTIONS.md` for the full list:

- How many bars on each side confirm a fractal swing point
  (`fractal_lookback`).
- What counts as a "strong candle body closure" / minimum displacement
  size for Step 5 (`min_displacement_ticks`).
- How close price must return to the Step 2 order block to count as
  "in the zone" for Step 4 (`zone_tolerance_ticks`).
- What exactly invalidates an in-progress setup (e.g., the hot zone being
  fully violated before Step 5 fires, or price never returning to retest
  the 1m Last Opposite Push within some reasonable window).

Until these are calibrated against real annotated chart examples, treat
scanner output as a hypothesis to sanity-check by eye, not a ready-to-fire
signal — see the shadow-period recommendation in `docs/OPEN_QUESTIONS.md`.
