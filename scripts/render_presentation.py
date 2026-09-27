#!/usr/bin/env python3
"""Maintainer-only local browser export; CI checks the committed bytes."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Optional local Chromium executable")
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright
    config = json.loads((ROOT / "presentation/config.json").read_text(encoding="utf-8"))
    assets = []
    def save(kind: str, data: bytes, width: int, height: int) -> None:
        digest = hashlib.sha256(data).hexdigest()
        prefix = {"social": "social-" + config["brand"], "touch": "apple-touch-icon", "favicon": "favicon-" + config["brand"], "icon192": "icon-" + config["brand"]}[kind]
        path = "site/" + prefix + "-" + digest[:12] + ".png"
        (ROOT / path).write_bytes(data)
        assets.append({"kind": kind, "path": path, "sha256": digest, "width": width, "height": height})
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, **({"executable_path": args.browser} if args.browser else {}))
        page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        page.goto((ROOT / "presentation/card.html").as_uri())
        page.evaluate("document.fonts.ready")
        assert page.evaluate("document.fonts.check('23px Inter') && document.fonts.check('80px \"Crimson Pro\"') && document.fonts.check('14px \"JetBrains Mono\"')")
        save("social", page.locator(".card").screenshot(animations="disabled"), 1200, 630)
        mark = (ROOT / "site" / config["favicon"]).read_text(encoding="utf-8")
        for kind, size in [("touch", 180), ("favicon", 32), ("icon192", 192)]:
            page.set_viewport_size({"width": size, "height": size})
            page.set_content(f'<style>html,body{{margin:0;background:#173b2d}}svg{{display:block;width:{size}px;height:{size}px;background:#173b2d}}</style>' + mark)
            save(kind, page.screenshot(animations="disabled", omit_background=False), size, size)
        renderer = {"tool": "Playwright Chromium", "playwright": importlib.metadata.version("playwright"), "browser": browser.version}
        browser.close()
    sources = ["presentation/card.html", "presentation/config.json", "scripts/render_presentation.py", "site/" + config["favicon"], *["site/fonts/" + name for name in ["inter-latin-variable.woff2", "crimson-pro-latin-variable.woff2", "crimson-pro-latin-italic-400.woff2", "jetbrains-mono-latin-variable.woff2"]]]
    manifest = {"schema_version": 1, "renderer": renderer, "sources": [{"path": f, "sha256": hashlib.sha256((ROOT / f).read_bytes()).hexdigest()} for f in sources], "assets": assets}
    (ROOT / "presentation/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    for asset in assets:
        print(asset["kind"], asset["path"], asset["sha256"])

if __name__ == "__main__":
    main()
