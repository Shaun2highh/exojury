"""Screenshot every app page at two widths + report JS console errors.

Assumes the app is running on :8501.
Run:  python -m exojury.screenshots
"""

import time

from playwright.sync_api import sync_playwright

from . import config

OUT = config.PROJECT_ROOT / "submission" / "screenshots"
PAGES = [
    ("", "0_home"),
    ("trial", "1_trial"),
    ("frontier", "2_frontier"),
    ("sky", "3_skymap"),
    ("audit", "4_audit"),
    ("methods", "5_methods"),
]
WIDTHS = [(1440, 1000, ""), (1080, 900, "_narrow")]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for width, height, suffix in WIDTHS:
            page = browser.new_page(viewport={"width": width, "height": height},
                                    device_scale_factor=2)
            page.on("console", lambda m: errors.append(m.text)
                    if m.type in ("error",) else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            for url_path, fname in PAGES:
                page.goto(f"http://localhost:8501/{url_path}",
                          wait_until="domcontentloaded")
                time.sleep(9)
                page.screenshot(path=OUT / f"{fname}{suffix}.png",
                                full_page=False)
                print(f"saved {fname}{suffix}.png")
            page.close()
        browser.close()
    if errors:
        print("\nJS console errors:")
        for e in dict.fromkeys(errors):
            print(" -", e[:200])
    else:
        print("\nNo JS console errors.")


if __name__ == "__main__":
    main()
