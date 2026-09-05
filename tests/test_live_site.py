from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate_live_site as live  # type: ignore


def response(status: int, body: str, **headers: str) -> live.Response:
    return live.Response(status=status, body=body, headers=headers)


def install_responses(
    monkeypatch, *, beacon: bool = False, www_status: int = 301
) -> None:
    html = "Train for the life"
    missing = "This path does not cross."
    if beacon:
        html += '<script data-cf-beacon="injected"></script>'
    responses = {
        f"{live.APEX}/": response(
            200,
            html,
            **{
                **live.EXPECTED_CONTENT_HEADERS,
                "cache-control": "no-transform, public, max-age=0, must-revalidate",
                "content-type": "text/html; charset=utf-8",
            },
        ),
        f"{live.APEX}/__bridge_missing_route_probe__": response(
            404,
            missing,
            **{
                **live.EXPECTED_CONTENT_HEADERS,
                "cache-control": "no-store, no-transform",
                "content-type": "text/html; charset=utf-8",
            },
        ),
    }
    for host in ("www.thebridgemethod.net", "the-bridge-method.pages.dev"):
        responses[f"https://{host}/audit-path?source=the-bridge-method"] = response(
            www_status if host == "www.thebridgemethod.net" else 301,
            "",
            location="https://thebridgemethod.net/audit-path?source=the-bridge-method",
            **live.EXPECTED_REDIRECT_HEADERS,
        )
    monkeypatch.setattr(live, "fetch", responses.__getitem__)


def test_live_contract_passes(monkeypatch) -> None:
    install_responses(monkeypatch)
    assert live.validate_live() == []


def test_live_contract_rejects_injected_beacon(monkeypatch) -> None:
    install_responses(monkeypatch, beacon=True)
    assert any("analytics beacon" in finding for finding in live.validate_live())


def test_live_contract_rejects_www_content_alias(monkeypatch) -> None:
    install_responses(monkeypatch, www_status=200)
    assert any("www must return 301" in finding for finding in live.validate_live())


def test_live_contract_rejects_cache_directive_spoof(monkeypatch) -> None:
    install_responses(monkeypatch)
    original = live.fetch

    def spoofed_fetch(url: str) -> live.Response:
        observed = original(url)
        if url == f"{live.APEX}/":
            return live.Response(
                status=observed.status,
                body=observed.body,
                headers={
                    **observed.headers,
                    "cache-control": "public, max-age=31536000, immutable, x-no-transform=yes",
                },
            )
        return observed

    monkeypatch.setattr(live, "fetch", spoofed_fetch)
    assert any(
        "homepage cache policy drifted" in finding for finding in live.validate_live()
    )


def test_live_contract_rejects_non_html_content(monkeypatch) -> None:
    install_responses(monkeypatch)
    original = live.fetch

    def wrong_type_fetch(url: str) -> live.Response:
        observed = original(url)
        if url == f"{live.APEX}/":
            return live.Response(
                status=observed.status,
                body=observed.body,
                headers={**observed.headers, "content-type": "text/html-invalid"},
            )
        return observed

    monkeypatch.setattr(live, "fetch", wrong_type_fetch)
    assert any("homepage content-type" in finding for finding in live.validate_live())


def test_live_contract_rejects_content_security_header_drift(monkeypatch) -> None:
    install_responses(monkeypatch)
    original = live.fetch

    def weakened_fetch(url: str) -> live.Response:
        observed = original(url)
        if url == f"{live.APEX}/":
            return live.Response(
                status=observed.status,
                body=observed.body,
                headers={**observed.headers, "referrer-policy": "unsafe-url"},
            )
        return observed

    monkeypatch.setattr(live, "fetch", weakened_fetch)
    assert any(
        "homepage referrer-policy drifted" in finding
        for finding in live.validate_live()
    )
