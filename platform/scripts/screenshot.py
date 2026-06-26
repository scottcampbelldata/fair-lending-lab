"""Capture deterministic desktop and mobile screenshots of the dashboard."""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:3001"
OUT = Path(__file__).resolve().parents[2] / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)

DESKTOP = (1440, 900)
MOBILE = (390, 844)


def shot(page, name: str, full_page: bool = True) -> None:
    out = OUT / f"{name}.png"
    page.screenshot(path=str(out), full_page=full_page)
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")


def main() -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx_desktop = browser.new_context(viewport={"width": DESKTOP[0], "height": DESKTOP[1]},
                                          device_scale_factor=2)
        page = ctx_desktop.new_page()
        page.goto(URL, wait_until="networkidle", timeout=30_000)
        # Recharts mount + first paint
        page.wait_for_selector("text=fair lending lab", timeout=10_000)
        page.wait_for_selector("text=Overview", timeout=10_000)
        time.sleep(2.0)
        shot(page, "dashboard_overview_desktop")

        page.get_by_role("button", name="Hypotheses", exact=True).click()
        time.sleep(1.5)
        shot(page, "dashboard_hypotheses_desktop")

        page.get_by_role("button", name="Family correction", exact=True).click()
        time.sleep(1.0)
        shot(page, "dashboard_family_desktop")

        page.get_by_role("button", name="Methods", exact=True).click()
        time.sleep(0.7)
        shot(page, "dashboard_methods_desktop")

        ctx_desktop.close()

        ctx_mobile = browser.new_context(viewport={"width": MOBILE[0], "height": MOBILE[1]},
                                         device_scale_factor=3,
                                         user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)")
        m = ctx_mobile.new_page()
        m.goto(URL, wait_until="networkidle", timeout=30_000)
        m.wait_for_selector("text=fair lending lab", timeout=10_000)
        time.sleep(1.5)
        shot(m, "dashboard_overview_mobile")

        m.get_by_role("button", name="Hypotheses", exact=True).click()
        time.sleep(1.5)
        shot(m, "dashboard_hypotheses_mobile")

        ctx_mobile.close()
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
