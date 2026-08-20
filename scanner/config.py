"""Loads config/*.yaml and .env into simple typed objects."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"


@dataclass
class InstrumentConfig:
    key: str
    name: str
    tick_size: float
    tick_value_usd: float
    tradovate_symbol: str
    htf_timeframes: list[str]
    ltf_timeframes: list[str]
    fractal_lookback: int
    min_displacement_ticks: int
    zone_tolerance_ticks: int
    stop_buffer_ticks: int
    timeout_bars_htf: int
    timeout_bars_ltf: int

    @property
    def min_displacement(self) -> float:
        return self.min_displacement_ticks * self.tick_size

    @property
    def zone_tolerance(self) -> float:
        return self.zone_tolerance_ticks * self.tick_size

    @property
    def stop_buffer(self) -> float:
        return self.stop_buffer_ticks * self.tick_size


@dataclass
class TradovateSettings:
    env: str
    client_id: str
    client_secret: str
    username: str
    password: str
    app_id: str
    app_version: str


@dataclass
class TelegramSettings:
    bot_token: str
    chat_id: str


@dataclass
class Settings:
    tradovate: TradovateSettings
    telegram: TelegramSettings
    vault_path: Path
    instruments: dict[str, InstrumentConfig]
    accounts: list[dict]
    rules: dict


def load_yaml(name: str) -> dict:
    path = CONFIG_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_instruments() -> dict[str, InstrumentConfig]:
    raw = load_yaml("instruments.yaml")["instruments"]
    result: dict[str, InstrumentConfig] = {}
    for key, spec in raw.items():
        result[key] = InstrumentConfig(
            key=key,
            name=spec["name"],
            tick_size=spec["tick_size"],
            tick_value_usd=spec["tick_value_usd"],
            tradovate_symbol=spec["tradovate_symbol"],
            htf_timeframes=spec["timeframes"]["htf"],
            ltf_timeframes=spec["timeframes"]["ltf"],
            fractal_lookback=spec["fractal_lookback"],
            min_displacement_ticks=spec["min_displacement_ticks"],
            zone_tolerance_ticks=spec["zone_tolerance_ticks"],
            stop_buffer_ticks=spec["stop_buffer_ticks"],
            timeout_bars_htf=spec["timeout_bars_htf"],
            timeout_bars_ltf=spec["timeout_bars_ltf"],
        )
    return result


def load_settings(env_file: str | Path | None = None) -> Settings:
    load_dotenv(env_file or (REPO_ROOT / ".env"))

    tradovate = TradovateSettings(
        env=os.getenv("TRADOVATE_ENV", "demo"),
        client_id=os.getenv("TRADOVATE_CLIENT_ID", ""),
        client_secret=os.getenv("TRADOVATE_CLIENT_SECRET", ""),
        username=os.getenv("TRADOVATE_USERNAME", ""),
        password=os.getenv("TRADOVATE_PASSWORD", ""),
        app_id=os.getenv("TRADOVATE_APP_ID", "ai-system"),
        app_version=os.getenv("TRADOVATE_APP_VERSION", "1.0"),
    )
    telegram = TelegramSettings(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
    )
    vault_path = Path(os.getenv("VAULT_PATH", str(REPO_ROOT / "vault")))

    return Settings(
        tradovate=tradovate,
        telegram=telegram,
        vault_path=vault_path,
        instruments=load_instruments(),
        accounts=load_yaml("accounts.yaml").get("accounts", []),
        rules=load_yaml("rules.yaml"),
    )
