"""Loads config/config.yaml, resolves the active profile, and applies environment overrides.

Precedence (highest first): process environment variables -> .env file -> config.yaml profile
defaults. This is what the assignment calls "Data-Driven ENV/profiles": the same code runs
against the "mock" or "live" profile purely by switching TEST_ENV, no code changes required.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config" / "config.yaml"


@dataclass(frozen=True)
class BrowserConfig:
    name: str
    headless: bool
    slow_mo_ms: int
    viewport_width: int
    viewport_height: int


@dataclass(frozen=True)
class EnvConfig:
    profile: str
    base_url: str
    currency_symbol: str
    search_path: str
    request_timeout_ms: int
    browser: BrowserConfig
    screenshots_dir: Path
    allure_results_dir: Path


def _read_yaml() -> dict[str, Any]:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_config(profile: str | None = None) -> EnvConfig:
    """Builds an EnvConfig for the given profile (or TEST_ENV / default_profile)."""
    load_dotenv(_PROJECT_ROOT / ".env", override=False)

    raw = _read_yaml()
    active_profile = profile or os.getenv("TEST_ENV") or raw["default_profile"]

    if active_profile not in raw["profiles"]:
        available = ", ".join(raw["profiles"].keys())
        raise ValueError(f"Unknown TEST_ENV profile '{active_profile}'. Available: {available}")

    profile_cfg = raw["profiles"][active_profile]
    browser_cfg = raw["browser"]

    return EnvConfig(
        profile=active_profile,
        base_url=os.getenv("BASE_URL", profile_cfg["base_url"]),
        currency_symbol=profile_cfg["currency_symbol"],
        search_path=profile_cfg["search_path"],
        request_timeout_ms=int(profile_cfg["request_timeout_ms"]),
        browser=BrowserConfig(
            name=os.getenv("BROWSER", browser_cfg["name"]),
            headless=os.getenv("HEADLESS", str(browser_cfg["headless"])).lower() == "true",
            slow_mo_ms=int(os.getenv("SLOW_MO_MS", browser_cfg["slow_mo_ms"])),
            viewport_width=int(browser_cfg["viewport"]["width"]),
            viewport_height=int(browser_cfg["viewport"]["height"]),
        ),
        screenshots_dir=_PROJECT_ROOT / raw["paths"]["screenshots_dir"],
        allure_results_dir=_PROJECT_ROOT / raw["paths"]["allure_results_dir"],
    )
