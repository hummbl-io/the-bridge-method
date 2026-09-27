#!/usr/bin/env python3
"""Validate the source-controlled thebridgemethod.net public surface."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from validate_presentation import presentation_cache_rules, validate_presentation

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_ROOT = REPO_ROOT / "site"
METHOD_SOURCE_RECEIPT = REPO_ROOT / "evidence" / "method-source.json"
CANONICAL_URL = "https://thebridgemethod.net/"
EXPECTED_METHOD_SOURCE = {
    "repository": "hummbl-io/coaching",
    "visibility": "private",
    "ref": "ac2428bfc3c0373ab1956e4c83d6e93f0793906b",
    "artifacts": {
        "methodology/coaching-system/canon-v0.1.md": (
            "fbbf338d04f6053e2bf646d95c5fa3aecc0ad33dcaeb360e97e58bf4e9c54525"
        ),
        "methodology/coaching-system/human-flourishing-v0.1.md": (
            "f4a5131aa1780aac786902f7569e76f5a83e61f56f07bf52246bdcaef91ed038"
        ),
        "methodology/coaching-system/sense-readiness-v1.0.md": (
            "bee9f392515e31f842216a56be9e89744ebf0abb923e704ec50e2244ae16f835"
        ),
        "methodology/coaching-system/physical-task-bridge-v0.1.md": (
            "3baa282eaf140c2359f699e6bd2fe61281332998b7360beaa7b83c1cdceeb279"
        ),
        "methodology/coaching-system/client-as-agent-v0.1.md": (
            "4e24c959d16158e8abb12c422a20cb072ef9aa2a956124920f6c383fe7601927"
        ),
        "methodology/13d-framework.md": (
            "014742baa571ade06ab055e77da5eeffaf670aeb3e7cb5a740fcfb3f01a00125"
        ),
    },
}
EXPECTED_METHOD_METADATA = {
    "schema_version": 1,
    "method": "The Bridge Method",
    "public_definition_status": "declared",
    "declared_on": "2026-09-05",
    "owner": "Reuben Bowlby",
    "audience": [
        "people connecting training to meaningful real-world tasks",
        "coaches documenting bounded, reviewable decisions",
    ],
}
EXPECTED_METHOD_CLAIMS = {
    "decision_loop": {
        "claim": (
            "The governing loop is govern, observe, prepare, train, adapt, record, "
            "and review."
        ),
        "source_paths": ["methodology/coaching-system/canon-v0.1.md"],
        "status": "current",
    },
    "task_decision_review": {
        "claim": (
            "The method connects intent and goals to observable tasks, evidence, "
            "constraints, bounded decisions, observations, and review."
        ),
        "source_paths": [
            "methodology/coaching-system/canon-v0.1.md",
            "methodology/coaching-system/physical-task-bridge-v0.1.md",
        ],
        "status": "current",
    },
    "context_13d": {
        "claim": "13D is a broad context-discovery surface.",
        "source_paths": [
            "methodology/coaching-system/canon-v0.1.md",
            "methodology/13d-framework.md",
        ],
        "status": "current",
    },
    "sense_readiness": {
        "claim": (
            "SENSE is a bounded readiness view covering Sleep, Exercise, Nutrition, "
            "Soreness, and Emotional State."
        ),
        "source_paths": [
            "methodology/coaching-system/canon-v0.1.md",
            "methodology/coaching-system/sense-readiness-v1.0.md",
        ],
        "status": "current",
    },
    "client_agency": {
        "claim": (
            "Client as Agent preserves autonomy, informed participation, bounded "
            "authority, escalation, and shared review."
        ),
        "source_paths": [
            "methodology/coaching-system/canon-v0.1.md",
            "methodology/coaching-system/client-as-agent-v0.1.md",
        ],
        "status": "current",
    },
    "scope_boundary": {
        "claim": (
            "The coaching system does not diagnose, treat, medically clear, or "
            "replace qualified professional judgment."
        ),
        "source_paths": [
            "methodology/coaching-system/canon-v0.1.md",
            "methodology/coaching-system/human-flourishing-v0.1.md",
            "methodology/coaching-system/physical-task-bridge-v0.1.md",
        ],
        "status": "current",
    },
}
REQUIRED_FILES = {
    "404.html",
    "index.html",
    "fonts.css",
    "styles.css",
    "_headers",
    "_redirects",
    "_worker.js",
    "robots.txt",
    "sitemap.xml",
    "llms.txt",
    "fonts/OFL-Crimson-Pro.txt",
    "fonts/OFL-Inter.txt",
    "fonts/OFL-JetBrains-Mono.txt",
    "fonts/crimson-pro-latin-italic-400.woff2",
    "fonts/crimson-pro-latin-variable.woff2",
    "fonts/inter-latin-variable.woff2",
    "fonts/jetbrains-mono-latin-variable.woff2",
}
REQUIRED_TOKENS = {
    "paper": "#f7f8f4",
    "white": "#ffffff",
    "ink": "#102f24",
    "muted": "#52635b",
    "forest": "#173b2d",
    "green": "#26754b",
    "mint": "#e6eee5",
    "border": "#d3ded2",
}
REQUIRED_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
    "strict-transport-security": "max-age=31536000; includeSubDomains; preload",
    "permissions-policy": (
        "camera=(), microphone=(), geolocation=(), payment=(), interest-cohort=()"
    ),
    "content-security-policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
        "frame-ancestors 'none'; form-action 'self'; object-src 'none'; "
        "base-uri 'self'; upgrade-insecure-requests;"
    ),
}
REQUIRED_CACHE_RULES = {
    "/": "public, max-age=0, must-revalidate",
    "/*.html": "public, max-age=0, must-revalidate",
    "/*.css": "public, max-age=86400, stale-while-revalidate=86400",
    "/*.woff2": "public, max-age=31536000, immutable",
    "/favicon-bridge-d1573dd1a5af.svg": "public, max-age=31536000, immutable",
    "/sitemap.xml": "public, max-age=3600",
    "/llms.txt": "public, max-age=3600",
}
REQUIRED_REDIRECTS = {
    "/about": ("/#method", "301"),
    "/method": ("/#method", "301"),
    "/framework": ("/#framework", "301"),
    "/guardrails": ("/#boundaries", "301"),
    "/boundaries": ("/#boundaries", "301"),
    "/person": ("https://reubenbowlby.com/", "302"),
    "/system": ("https://hummbl.io/", "302"),
    "/proof": ("https://hummbl.io/proof", "302"),
    "/build": ("https://hummbl.io/build", "302"),
    "/house": ("https://hummbl.house/", "302"),
    "/rpbx": ("https://rpbx.net/", "302"),
}
REQUIRED_PUBLIC_COPY = {
    "The Bridge Method",
    "Reuben Bowlby",
    "govern",
    "observe",
    "prepare",
    "train",
    "adapt",
    "record",
    "review",
    "13D",
    "SENSE",
    "Physical Task Bridge",
    "Client as Agent",
}
FORBIDDEN_PUBLIC_CLAIMS = {
    "licensed attorney",
    "certified financial planner",
    "guaranteed outcome",
    "diagnose",
    "treat disease",
}


class SiteParser(HTMLParser):
    """Collect the small set of HTML facts enforced by this static site."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.stylesheets: list[str] = []
        self.icons: list[str] = []
        self.canonicals: list[str] = []
        self.h1_count = 0
        self.missing_image_alt = 0
        self.json_ld_blocks: list[str] = []
        self._in_json_ld = False
        self._json_ld_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.casefold(): value for name, value in attrs}
        if attributes.get("id"):
            self.ids.add(str(attributes["id"]))
        if tag.casefold() == "a" and attributes.get("href"):
            self.hrefs.append(str(attributes["href"]))
        if tag.casefold() == "link" and attributes.get("href"):
            rel = set(str(attributes.get("rel", "")).casefold().split())
            href = str(attributes["href"])
            if "stylesheet" in rel:
                self.stylesheets.append(href)
            if "icon" in rel and attributes.get("type") == "image/svg+xml":
                self.icons.append(href)
            if "canonical" in rel:
                self.canonicals.append(href)
        if tag.casefold() == "h1":
            self.h1_count += 1
        if tag.casefold() == "img" and "alt" not in attributes:
            self.missing_image_alt += 1
        if (
            tag.casefold() == "script"
            and attributes.get("type") == "application/ld+json"
        ):
            self._in_json_ld = True
            self._json_ld_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "script" and self._in_json_ld:
            self.json_ld_blocks.append("".join(self._json_ld_parts))
            self._in_json_ld = False

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._json_ld_parts.append(data)


def _top_level_root_blocks(source: str) -> list[str]:
    uncommented = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    blocks: list[str] = []
    depth = 0
    selector_start = 0
    root_body_start: int | None = None
    for index, character in enumerate(uncommented):
        if character == "{":
            selector = uncommented[selector_start:index].strip()
            if depth == 0 and selector == ":root":
                root_body_start = index + 1
            depth += 1
            selector_start = index + 1
        elif character == "}":
            if depth == 1 and root_body_start is not None:
                blocks.append(uncommented[root_body_start:index])
                root_body_start = None
            depth = max(0, depth - 1)
            selector_start = index + 1
    return blocks


def _root_tokens(source: str) -> dict[str, list[str]]:
    declarations: dict[str, list[str]] = {name: [] for name in REQUIRED_TOKENS}
    for block in _top_level_root_blocks(source):
        if "{" in block or "}" in block:
            continue
        for name, value in re.findall(r"--([\w-]+)\s*:\s*([^;{}]+)(?:;|$)", block):
            if name in declarations:
                declarations[name].append(value.strip())
    return declarations


def _all_required_token_declarations(source: str) -> dict[str, list[str]]:
    """Collect required token declarations from every active CSS context."""
    uncommented = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return {
        name: [
            value.strip()
            for value in re.findall(
                rf"--{re.escape(name)}\s*:\s*([^;{{}}]+)(?:;|(?=\}}))",
                uncommented,
            )
        ]
        for name in REQUIRED_TOKENS
    }


def _header_rules(source: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Parse the deterministic subset of Cloudflare Pages _headers in use."""
    rules: dict[str, dict[str, str]] = {}
    failures: list[str] = []
    current: str | None = None
    for raw_line in source.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw_line == raw_line.lstrip():
            current = stripped
            if current in rules:
                failures.append(f"_headers duplicate rule block: {current}")
            else:
                rules[current] = {}
            continue
        if stripped.startswith("! "):
            failures.append(f"_headers detach directives are forbidden: {stripped}")
            continue
        if current is None or ":" not in stripped:
            failures.append(f"_headers malformed directive: {stripped}")
            continue
        name, value = stripped.split(":", 1)
        normalized_name = name.casefold()
        if normalized_name in rules[current]:
            failures.append(f"_headers duplicate {name} in rule {current}")
        else:
            rules[current][normalized_name] = value.strip()
    return rules, failures


def _redirect_rules(source: str) -> tuple[dict[str, tuple[str, str]], list[str]]:
    rules: dict[str, tuple[str, str]] = {}
    failures: list[str] = []
    for raw_line in source.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) != 3:
            failures.append(f"_redirects malformed rule: {stripped}")
            continue
        if parts[0] in rules:
            failures.append(f"_redirects duplicate source: {parts[0]}")
            continue
        rules[parts[0]] = (parts[1], parts[2])
    return rules, failures


def validate_method_source(path: Path = METHOD_SOURCE_RECEIPT) -> list[str]:
    """Validate the declaration that bounds public method claims."""
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"method source receipt is unreadable: {error}"]

    failures: list[str] = []
    for field, expected in EXPECTED_METHOD_METADATA.items():
        observed = receipt.get(field)
        if (
            field == "schema_version"
            and (type(observed) is not int or observed != expected)
        ) or (field != "schema_version" and observed != expected):
            failures.append(f"method source {field} must equal {expected}")
    source = receipt.get("source", {})
    for field in ("repository", "visibility", "ref"):
        expected = EXPECTED_METHOD_SOURCE[field]
        if source.get(field) != expected:
            failures.append(f"method source {field} must equal {expected}")

    artifacts = source.get("artifacts", [])
    observed_artifacts = {
        item.get("path"): item.get("sha256")
        for item in artifacts
        if isinstance(item, dict)
    }
    if observed_artifacts != EXPECTED_METHOD_SOURCE["artifacts"]:
        failures.append(
            "method source artifacts must match the approved coaching canon"
        )
    if len(artifacts) != len(observed_artifacts):
        failures.append("method source artifact paths must be unique")

    claims = receipt.get("public_claims", [])
    observed_claims = {
        claim.get("id"): {
            "claim": claim.get("claim"),
            "source_paths": claim.get("source_paths"),
            "status": claim.get("status"),
        }
        for claim in claims
        if isinstance(claim, dict)
    }
    if observed_claims != EXPECTED_METHOD_CLAIMS:
        failures.append("method source claims must match the approved public claim map")
    if len(claims) != len(observed_claims):
        failures.append("method source claim ids must be unique")
    return failures


def validate_site(site_root: Path = SITE_ROOT) -> list[str]:
    """Return deterministic findings for the public site tree."""
    failures = validate_method_source()
    for name in sorted(REQUIRED_FILES):
        if not (site_root / name).is_file():
            failures.append(f"missing required site file: {name}")
    if failures:
        return failures

    html = (site_root / "index.html").read_text(encoding="utf-8")
    parser = SiteParser()
    parser.feed(html)

    not_found_html = (site_root / "404.html").read_text(encoding="utf-8")
    not_found_parser = SiteParser()
    not_found_parser.feed(not_found_html)

    if parser.canonicals != [CANONICAL_URL]:
        failures.append(f"canonical link must be exactly {CANONICAL_URL}")
    if parser.h1_count != 1:
        failures.append("index.html must contain exactly one h1")
    if parser.missing_image_alt:
        failures.append("every image must have an alt attribute")
    if not_found_parser.h1_count != 1:
        failures.append("404.html must contain exactly one h1")
    if not_found_parser.canonicals:
        failures.append("404.html must not declare a canonical URL")
    if 'name="robots" content="noindex, follow"' not in not_found_html:
        failures.append("404.html must declare noindex, follow")
    if not_found_parser.stylesheets != ["/fonts.css?v=1", "/styles.css?v=2"]:
        failures.append("404.html must use the versioned global site URLs")
    if "mailto:" in (html + not_found_html).casefold():
        failures.append("mailto links are forbidden")
    if parser.stylesheets != ["/fonts.css?v=1", "/styles.css?v=2"]:
        failures.append("stylesheets must use the versioned global site URLs")
    if not any(urlparse(href).hostname == "hummbl.io" for href in parser.hrefs):
        failures.append("site must link to hummbl.io")
    if not any(urlparse(href).hostname == "reubenbowlby.com" for href in parser.hrefs):
        failures.append("site must link to reubenbowlby.com")
    if not any(urlparse(href).hostname == "hummbl.house" for href in parser.hrefs):
        failures.append("site must link to hummbl.house")
    if not any(urlparse(href).hostname == "rpbx.net" for href in parser.hrefs):
        failures.append("site must link to rpbx.net")
    for required_copy in sorted(REQUIRED_PUBLIC_COPY):
        if required_copy not in html:
            failures.append(
                f"index.html missing canonical public copy: {required_copy}"
            )
    lowered_html = html.casefold()
    for forbidden_claim in sorted(FORBIDDEN_PUBLIC_CLAIMS):
        if forbidden_claim in lowered_html:
            failures.append(
                f"index.html contains forbidden unsupported claim: {forbidden_claim}"
            )

    for href in parser.hrefs:
        if href.startswith("#") and href[1:] not in parser.ids:
            failures.append(f"fragment target does not exist: {href}")
        parsed = urlparse(href)
        if parsed.scheme == "http":
            failures.append(f"insecure external link: {href}")

    for href in not_found_parser.hrefs:
        if href.startswith("#") and href[1:] not in not_found_parser.ids:
            failures.append(f"404 fragment target does not exist: {href}")
        parsed = urlparse(href)
        if parsed.scheme == "http":
            failures.append(f"404 contains insecure external link: {href}")

    local_assets = parser.stylesheets + parser.icons
    for asset in local_assets:
        parsed = urlparse(asset)
        if parsed.scheme or parsed.netloc:
            failures.append(f"site asset must be self-hosted: {asset}")
            continue
        path = site_root / parsed.path.lstrip("/")
        if not path.is_file():
            failures.append(f"referenced local asset does not exist: {asset}")

    not_found_assets = not_found_parser.stylesheets + not_found_parser.icons
    for asset in not_found_assets:
        parsed = urlparse(asset)
        if parsed.scheme or parsed.netloc:
            failures.append(f"404 asset must be self-hosted: {asset}")
            continue
        path = site_root / parsed.path.lstrip("/")
        if not path.is_file():
            failures.append(f"404 referenced local asset does not exist: {asset}")

    if not_found_parser.icons != parser.icons:
        failures.append(
            "404.html must use the same content-addressed favicon as index.html"
        )

    if len(parser.icons) != 1:
        failures.append("exactly one SVG favicon is required")
    else:
        icon_path = urlparse(parser.icons[0]).path.lstrip("/")
        match = re.fullmatch(r"favicon-bridge-([0-9a-f]{12})\.svg", icon_path)
        if not match:
            failures.append("favicon filename must be content-addressed")
        else:
            icon_file = site_root / icon_path
            if icon_file.is_file():
                digest = hashlib.sha256(icon_file.read_bytes()).hexdigest()
                if digest[:12] != match.group(1):
                    failures.append("favicon filename hash does not match its content")

    if not parser.json_ld_blocks:
        failures.append("JSON-LD website metadata is required")
    for block in parser.json_ld_blocks:
        try:
            metadata = json.loads(block)
        except json.JSONDecodeError as exc:
            failures.append(f"invalid JSON-LD: {exc.msg}")
            continue
        if metadata.get("@type") != "WebSite" or metadata.get("url") != CANONICAL_URL:
            failures.append(
                "JSON-LD must identify the canonical The Bridge Method WebSite"
            )
        creator = metadata.get("creator", {})
        if creator.get("url") != "https://reubenbowlby.com/":
            failures.append("JSON-LD creator must identify Reuben's canonical site")

    css = (site_root / "styles.css").read_text(encoding="utf-8")
    tokens = _root_tokens(css)
    all_token_declarations = _all_required_token_declarations(css)
    for name, value in REQUIRED_TOKENS.items():
        if tokens[name] != [value]:
            failures.append(f"styles.css: --{name} must have one root value {value}")
        if all_token_declarations[name] != [value]:
            failures.append(
                f"styles.css: --{name} must not be redeclared outside its root profile"
            )
    for required in (":focus-visible", "prefers-reduced-motion", "max-width: 390px"):
        if required not in css:
            failures.append(f"styles.css missing interaction rule: {required}")

    headers = (site_root / "_headers").read_text(encoding="utf-8")
    header_rules, header_parse_failures = _header_rules(headers)
    failures.extend(header_parse_failures)
    expected_header_patterns = set(REQUIRED_CACHE_RULES) | {"/*"}
    if set(header_rules) != expected_header_patterns:
        failures.append(
            "_headers rule patterns must exactly match the governed policy map"
        )
    global_headers = header_rules.get("/*", {})
    for name, expected in REQUIRED_HEADERS.items():
        if global_headers.get(name) != expected:
            failures.append(f"_headers global {name} policy must equal {expected}")
    if global_headers.get("cache-control") != "no-transform":
        failures.append("_headers global Cache-Control policy must equal no-transform")
    for path, expected in REQUIRED_CACHE_RULES.items():
        expected_assignment = {"cache-control": expected}
        if header_rules.get(path) != expected_assignment:
            failures.append(
                f"_headers rule for {path} must contain only Cache-Control: {expected}"
            )

    redirects = (site_root / "_redirects").read_text(encoding="utf-8")
    redirect_rules, redirect_parse_failures = _redirect_rules(redirects)
    failures.extend(redirect_parse_failures)
    if redirect_rules != REQUIRED_REDIRECTS:
        failures.append("_redirects must exactly match the governed legacy route map")

    worker = (site_root / "_worker.js").read_text(encoding="utf-8")
    for required in (
        'const CANONICAL_HOST = "thebridgemethod.net";',
        '"www.thebridgemethod.net"',
        '"the-bridge-method.pages.dev"',
        "ALIAS_HOSTS.has(url.hostname)",
        "protectHtml(response)",
        "status: 301",
    ):
        if required not in worker:
            failures.append(
                f"_worker.js missing canonical routing contract: {required}"
            )

    sitemap = (site_root / "sitemap.xml").read_text(encoding="utf-8")
    if CANONICAL_URL not in sitemap:
        failures.append("sitemap must contain the canonical URL")
    failures.extend(validate_presentation(site_root))
    return failures


REQUIRED_CACHE_RULES.update(presentation_cache_rules())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=SITE_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    failures = validate_site(args.root)
    if failures:
        print(f"Site validation failed ({len(failures)} finding(s)):")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS: thebridgemethod.net source, routes, design, metadata, and edge policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
