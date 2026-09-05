#!/usr/bin/env python3
"""Fail closed when the deployed thebridgemethod.net surface drifts from its contract."""

from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

APEX = "https://thebridgemethod.net"
EXPECTED_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
    "frame-ancestors 'none'; form-action 'self'; object-src 'none'; "
    "base-uri 'self'; upgrade-insecure-requests;"
)
EXPECTED_CONTENT_HEADERS = {
    "content-security-policy": EXPECTED_CSP,
    "cross-origin-opener-policy": "same-origin",
    "cross-origin-resource-policy": "same-origin",
    "permissions-policy": (
        "camera=(), microphone=(), geolocation=(), payment=(), interest-cohort=()"
    ),
    "referrer-policy": "strict-origin-when-cross-origin",
    "strict-transport-security": "max-age=31536000; includeSubDomains; preload",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "x-permitted-cross-domain-policies": "none",
}
EXPECTED_REDIRECT_HEADERS = {
    "cache-control": "public, max-age=3600",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none';",
    "referrer-policy": "strict-origin-when-cross-origin",
    "strict-transport-security": "max-age=31536000; includeSubDomains; preload",
    "x-content-type-options": "nosniff",
}
BEACON_MARKERS = ("data-cf-beacon", "static.cloudflareinsights.com/beacon")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Expose redirect status and Location instead of following it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict[str, str]
    body: str


def fetch(url: str) -> Response:
    request = urllib.request.Request(
        url, headers={"User-Agent": "the-bridge-method-live-audit/1"}
    )
    opener = urllib.request.build_opener(NoRedirect)
    try:
        result = opener.open(request, timeout=20)
    except urllib.error.HTTPError as error:
        result = error
    with result:
        body = result.read().decode("utf-8", errors="replace")
        return Response(
            status=result.status,
            headers={name.casefold(): value for name, value in result.headers.items()},
            body=body,
        )


def cache_directives(value: str) -> set[str]:
    return {
        directive.strip().casefold()
        for directive in value.split(",")
        if directive.strip()
    }


def validate_live() -> list[str]:
    findings: list[str] = []
    homepage = fetch(f"{APEX}/")
    missing = fetch(f"{APEX}/__bridge_missing_route_probe__")
    www = fetch("https://www.thebridgemethod.net/audit-path?source=the-bridge-method")
    pages = fetch(
        "https://the-bridge-method.pages.dev/audit-path?source=the-bridge-method"
    )

    if homepage.status != 200:
        findings.append(f"homepage status must be 200, observed {homepage.status}")
    if "Train for the life" not in homepage.body:
        findings.append("homepage deployment marker is missing")
    if missing.status != 404:
        findings.append(f"unknown route status must be 404, observed {missing.status}")
    if "This path does not cross." not in missing.body:
        findings.append("unknown route must serve the governed 404 page")

    for name, response in (("homepage", homepage), ("404", missing)):
        lowered = response.body.casefold()
        if any(marker in lowered for marker in BEACON_MARKERS):
            findings.append(f"{name} contains an injected Cloudflare analytics beacon")
        for header, expected in EXPECTED_CONTENT_HEADERS.items():
            if response.headers.get(header) != expected:
                findings.append(f"{name} {header} drifted")
        media_type = (
            response.headers.get("content-type", "").split(";", 1)[0].strip().casefold()
        )
        if media_type != "text/html":
            findings.append(f"{name} content-type must be text/html")
        observed_cache = cache_directives(response.headers.get("cache-control", ""))
        expected_cache = (
            {"public", "max-age=0", "must-revalidate", "no-transform"}
            if name == "homepage"
            else {"no-store", "no-transform"}
        )
        if observed_cache != expected_cache:
            findings.append(f"{name} cache policy drifted")

    expected_location = (
        "https://thebridgemethod.net/audit-path?source=the-bridge-method"
    )
    for name, response in (("www", www), ("pages.dev", pages)):
        if response.status != 301:
            findings.append(f"{name} must return 301, observed {response.status}")
        if response.headers.get("location") != expected_location:
            findings.append(f"{name} redirect must preserve the path and query string")
        for header, expected in EXPECTED_REDIRECT_HEADERS.items():
            if response.headers.get(header) != expected:
                findings.append(f"{name} redirect {header} policy drifted")
    return findings


def main() -> int:
    for attempt in range(1, 7):
        try:
            findings = validate_live()
        except (OSError, TimeoutError) as error:
            findings = [f"live audit request failed: {error}"]
        if not findings:
            print("PASS: live thebridgemethod.net routes and edge policy")
            return 0
        if attempt < 6:
            time.sleep(5)
    print(f"Live site validation failed ({len(findings)} finding(s)):")
    for finding in findings:
        print(f"- {finding}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
