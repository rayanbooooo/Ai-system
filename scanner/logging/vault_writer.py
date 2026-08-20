"""Writes vault/Signals/*.md whenever the state machine fires a Setup -
every Telegram alert also gets a searchable note, per the user's request.
"""
from __future__ import annotations

from pathlib import Path

from scanner.structure.models import Direction, Setup

_SIGNAL_FRONTMATTER = """---
type: signal
instrument: {instrument}
direction: {direction}
step_chain: [1, 2, 3, 4, 5, 6]
entry: {entry}
stop_loss: {stop_loss}
take_profit: {take_profit}
triggered_at: {triggered_at}
accounts_notified: {accounts_notified}
outcome: pending
executed: false
---
"""


def write_signal_note(vault_path: Path, setup: Setup, accounts_notified: list[str]) -> Path:
    direction_label = "long" if setup.direction == Direction.BULLISH else "short"
    filename = f"{setup.triggered_at:%Y-%m-%d}-{setup.instrument}-{direction_label}-{setup.triggered_at:%H%M}.md"
    path = vault_path / "Signals" / filename
    path.parent.mkdir(parents=True, exist_ok=True)

    frontmatter = _SIGNAL_FRONTMATTER.format(
        instrument=setup.instrument,
        direction=direction_label,
        entry=f"{setup.entry:.2f}",
        stop_loss=f"{setup.stop_loss:.2f}",
        take_profit=f"{setup.take_profit:.2f}",
        triggered_at=setup.triggered_at.isoformat(),
        accounts_notified=accounts_notified,
    )
    body = (
        f"\n# {setup.instrument} {direction_label} — {setup.triggered_at:%Y-%m-%d %H:%M}\n\n"
        "Auto-written by scanner/logging/vault_writer.py when Step 6 fired.\n\n"
        "## Structure Chain\n\n"
        f"- Step 1 (HTF BOS): {setup.step1_solidified_point.pivot.price:.2f} "
        f"@ {setup.step1_solidified_point.pivot.timestamp:%Y-%m-%d %H:%M} ({setup.step1_htf_timeframe})\n"
        f"- Step 2 (Order Block): {setup.step2_order_block.low:.2f}-{setup.step2_order_block.high:.2f} "
        f"@ {setup.step2_order_block.bar.timestamp:%Y-%m-%d %H:%M}\n"
        f"- Step 3 (Solidified Target / TP anchor): {setup.step3_target.pivot.price:.2f}\n"
        f"- Step 4 (Zone Retracement): {setup.step4_zone.low:.2f}-{setup.step4_zone.high:.2f}\n"
        f"- Step 5 (1m Displacement): {setup.step5_displacement_bar.timestamp:%H:%M}, "
        f"Last Opposite Push {setup.step5_last_opposite_push.low:.2f}-{setup.step5_last_opposite_push.high:.2f}\n"
        f"- Step 6 (Retest Entry): {setup.entry:.2f}\n\n"
        "## Outcome\n\n"
        "- [ ] Executed\n"
        "- Result:\n"
        "- Notes:\n"
    )
    path.write_text(frontmatter + body, encoding="utf-8")
    return path
