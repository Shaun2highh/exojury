"""Screenshot every dashboard tab (for Devpost gallery + design review).

Assumes the app is already running on :8501.
Run:  python -m exojury.screenshots
"""

import time

from playwright.sync_api import sync_playwright

from . import config

OUT = config.PROJECT_ROOT / "submission" / "screenshots"
TABS = [
    ("The Trial", "1_trial"),
    ("Frontier", "2_frontier"),
    ("Sky Map", "3_skymap"),
    ("The Audit", "4_audit"),
    ("Honesty", "5_honesty"),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000},
                                device_scale_factor=2)
        page.goto("http://localhost:8501", wait_until="networkidle")
        time.sleep(6)  # let plotly finish drawing
        for tab_text, fname in TABS:
            page.get_by_role("tab", name=tab_text).click()
            time.sleep(4)
            page.screenshot(path=OUT / f"{fname}.png", full_page=False)
            print(f"saved {fname}.png")
        browser.close()


if __name__ == "__main__":
    main()
