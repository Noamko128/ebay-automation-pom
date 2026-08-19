from __future__ import annotations

import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

import allure
import pytest
from playwright.sync_api import sync_playwright

from core.config_loader import EnvConfig, load_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _wait_for_server(base_url: str, timeout_s: float = 10.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            urllib.request.urlopen(base_url, timeout=1)
            return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.2)
    raise RuntimeError(f"Mock server did not become ready at {base_url} within {timeout_s}s")


@pytest.fixture(scope="session")
def config() -> EnvConfig:
    """Resolves the active profile and resets this session's artifact directories.

    Mirrors pytest.ini's --clean-alluredir: without this, a run that produces fewer
    screenshots/traces than a previous one (e.g. a test failing partway through) leaves stale
    files mixed in, misrepresenting what the latest run actually did.
    """
    cfg = load_config()

    if cfg.screenshots_dir.exists():
        shutil.rmtree(cfg.screenshots_dir)
    cfg.screenshots_dir.mkdir(parents=True, exist_ok=True)

    traces_dir = PROJECT_ROOT / "reports" / "traces"
    if traces_dir.exists():
        shutil.rmtree(traces_dir)
    traces_dir.mkdir(parents=True, exist_ok=True)

    return cfg


@pytest.fixture(scope="session", autouse=True)
def mock_server(config: EnvConfig):
    """Starts the bundled mock eBay app for the "mock" profile (the default). No-op for
    "live", where config.base_url already points at the real ebay.com."""
    if config.profile != "mock":
        yield
        return

    process = subprocess.Popen(
        [sys.executable, "-m", "mock_site.server"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_server(config.base_url)
        yield
    finally:
        process.terminate()
        process.wait(timeout=5)


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance, config: EnvConfig):
    browser_type = getattr(playwright_instance, config.browser.name)
    launched = browser_type.launch(headless=config.browser.headless, slow_mo=config.browser.slow_mo_ms)
    yield launched
    launched.close()


@pytest.fixture
def context(browser, config: EnvConfig, request):
    ctx = browser.new_context(
        viewport={"width": config.browser.viewport_width, "height": config.browser.viewport_height}
    )
    ctx.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield ctx

    traces_dir = PROJECT_ROOT / "reports" / "traces"
    trace_path = traces_dir / f"{request.node.name}.zip"
    ctx.tracing.stop(path=str(trace_path))
    if trace_path.exists():
        allure.attach.file(str(trace_path), name="trace", extension="zip")
    ctx.close()


@pytest.fixture
def page(context):
    pg = context.new_page()
    yield pg
    pg.close()
