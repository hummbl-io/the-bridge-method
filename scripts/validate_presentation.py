"""Exact asset, metadata and editable-source validation without image dependencies."""
from __future__ import annotations
import hashlib
import json
import struct
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def manifest() -> dict:
    return json.loads((ROOT / "presentation/manifest.json").read_text(encoding="utf-8"))

def presentation_cache_rules() -> dict[str, str]:
    return {"/" + asset["path"].removeprefix("site/"): "public, max-age=31536000, immutable" for asset in manifest()["assets"]}

class Metadata(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, list[str]] = {}
        self.links: list[dict[str, str | None]] = []
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "link": self.links.append(values)
        if tag == "meta":
            key = values.get("property") or values.get("name")
            if key: self.meta.setdefault(key, []).append(values.get("content") or "")

def validate_presentation(site_root: Path = ROOT / "site") -> list[str]:
    failures: list[str] = []
    data = manifest()
    config = json.loads((ROOT / "presentation/config.json").read_text(encoding="utf-8"))
    assets = {entry["kind"]: entry for entry in data["assets"]}
    sizes = {"social": (1200, 630), "touch": (180, 180), "favicon": (32, 32), "icon192": (192, 192)}
    if set(assets) != set(sizes) or len(data["assets"]) != 4: return ["presentation asset kinds differ"]
    for source in data["sources"]:
        if hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            failures.append("presentation source changed without reviewed render: " + source["path"])
    for kind, asset in assets.items():
        path = site_root / asset["path"].removeprefix("site/")
        if not path.is_file():
            failures.append("presentation asset missing: " + asset["path"]); continue
        png = path.read_bytes()
        digest = hashlib.sha256(png).hexdigest()
        if digest != asset["sha256"] or digest[:12] not in path.name:
            failures.append("presentation asset hash differs: " + asset["path"])
        if len(png) < 24 or png[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", png[16:24]) != sizes[kind]:
            failures.append("presentation PNG dimensions differ: " + kind)
    for document in ["index.html", "404.html"]:
        parser = Metadata(); parser.feed((site_root / document).read_text(encoding="utf-8"))
        for kind, rel, size in [("touch", "apple-touch-icon", "180x180"), ("favicon", "icon", "32x32"), ("icon192", "icon", "192x192")]:
            links = [link for link in parser.links if link.get("rel") == rel and link.get("sizes") == size]
            if len(links) != 1 or links[0].get("href") != "/" + assets[kind]["path"].removeprefix("site/"):
                failures.append(document + " must reference exact " + kind)
        if document == "index.html":
            image = "https://" + config["host"] + "/" + assets["social"]["path"].removeprefix("site/")
            for key, expected in {"og:image": image, "twitter:image": image, "og:image:alt": config["alt"], "og:url": "https://" + config["host"] + "/", "og:image:width": "1200", "og:image:height": "630", "twitter:card": "summary_large_image"}.items():
                if parser.meta.get(key) != [expected]: failures.append(document + " has incorrect " + key)
    return failures

def audit_live() -> list[str]:
    """Read the canonical homepage and four reviewed assets after deployment."""
    import urllib.error
    import urllib.request
    config = json.loads((ROOT / "presentation/config.json").read_text(encoding="utf-8"))
    base = "https://" + config["host"]
    failures: list[str] = []
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req: urllib.request.Request, fp: object, code: int, msg: str, headers: object, newurl: str) -> None:
            return None
    opener = urllib.request.build_opener(NoRedirect)
    for asset in [{"path": "site/index.html", "sha256": hashlib.sha256((ROOT / "site/index.html").read_bytes()).hexdigest(), "kind": "page"}, *manifest()["assets"]]:
        path = "/" if asset["kind"] == "page" else "/" + asset["path"].removeprefix("site/")
        request = urllib.request.Request(base + path, headers={"User-Agent": "presentation-live-audit/1"})
        try:
            response = opener.open(request, timeout=20)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read()
            if response.status != 200 or hashlib.sha256(body).hexdigest() != asset["sha256"]:
                failures.append(path + " response differs from reviewed bytes")
            if asset["kind"] != "page":
                if response.headers.get("Content-Type", "").split(";", 1)[0] != "image/png": failures.append(path + " PNG media type differs")
                directives = {item.strip() for item in response.headers.get("Cache-Control", "").split(",")}
                if directives != {"public", "max-age=31536000", "immutable", "no-transform"}: failures.append(path + " immutable cache differs")
                if response.headers.get("Content-Disposition"): failures.append(path + " must render inline")
    return failures

if __name__ == "__main__":
    import sys
    failures = validate_presentation()
    if "--live" in sys.argv:
        failures.extend(audit_live())
    for failure in failures:
        print("FAIL:", failure)
    if not failures: print("PASS: presentation source, assets and metadata" + (" plus live bytes" if "--live" in sys.argv else ""))
    raise SystemExit(bool(failures))
