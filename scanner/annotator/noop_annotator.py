"""Default annotator: logs what it would have drawn and does nothing live.
Used until a real CDP-backed annotator is confirmed buildable - see
docs/OPEN_QUESTIONS.md.
"""
from __future__ import annotations

import logging

from scanner.annotator.base import ChartAnnotator
from scanner.structure.models import Setup

logger = logging.getLogger(__name__)


class NoopAnnotator(ChartAnnotator):
    def draw_setup(self, setup: Setup) -> None:
        logger.info(
            "NoopAnnotator: would draw %s %s setup (entry=%.2f, sl=%.2f, tp=%.2f) - "
            "no live chart connection wired up yet, see docs/OPEN_QUESTIONS.md",
            setup.instrument,
            setup.direction.value,
            setup.entry,
            setup.stop_loss,
            setup.take_profit,
        )
