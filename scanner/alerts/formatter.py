"""Setup -> human-readable alert text (Telegram message + vault note body)."""
from __future__ import annotations

from scanner.structure.models import Direction, Setup


def format_setup_message(setup: Setup, vault_link: str = "") -> str:
    direction_label = "LONG" if setup.direction == Direction.BULLISH else "SHORT"
    rr = setup.risk_reward
    lines = [
        f"A+ SETUP — {setup.instrument} {direction_label}",
        "Triggered: Step 6 (Retest Entry)",
        f"Entry: {setup.entry:.2f} (limit, retest of 1m Last Opposite Push)",
        f"Stop Loss: {setup.stop_loss:.2f} (beyond 1m anchor)",
        f"Take Profit: {setup.take_profit:.2f} (Step 3 Solidified {'High' if setup.direction == Direction.BULLISH else 'Low'})",
        f"R:R ~ 1:{rr:.1f}",
        f"HTF: {setup.step1_htf_timeframe} BOS {setup.step1_solidified_point.pivot.timestamp:%H:%M} "
        f"| Zone confirmed {setup.step4_zone.confirmed_at_index}",
        f"Time: {setup.triggered_at:%Y-%m-%d %H:%M:%S}",
        "Manual execution required — verify on TradingView/Tradovate before entering.",
    ]
    if vault_link:
        lines.append(f"Logged: {vault_link}")
    return "\n".join(lines)
