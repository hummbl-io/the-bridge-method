from __future__ import annotations
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from validate_presentation import validate_presentation

class PresentationTests(unittest.TestCase):
    def test_reviewed_metadata_and_asset_hashes_pass(self) -> None:
        self.assertEqual(validate_presentation(), [])
    def test_misdirected_card_and_changed_png_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "site"; shutil.copytree(ROOT / "site", copy)
            config = json.loads((ROOT / "presentation/config.json").read_text(encoding="utf-8"))
            page = copy / "index.html"
            page.write_text(page.read_text(encoding="utf-8").replace("https://" + config["host"] + "/social-", "https://example.com/social-"), encoding="utf-8")
            data = json.loads((ROOT / "presentation/manifest.json").read_text(encoding="utf-8"))
            png = copy / data["assets"][0]["path"].removeprefix("site/")
            png.write_bytes(png.read_bytes() + b"tampered")
            failures = validate_presentation(copy)
            self.assertTrue(any("og:image" in f for f in failures))
            self.assertTrue(any("asset hash differs" in f for f in failures))
