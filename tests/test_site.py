from __future__ import annotations

import shutil
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate_site as validator  # type: ignore


def copy_site(tmp_path: Path) -> Path:
    target = tmp_path / "site"
    shutil.copytree(validator.SITE_ROOT, target)
    return target


def test_repository_site_passes() -> None:
    assert validator.validate_site() == []


def test_method_claims_are_bound_to_exact_canon(monkeypatch, tmp_path: Path) -> None:
    receipt = json.loads(validator.METHOD_SOURCE_RECEIPT.read_text(encoding="utf-8"))
    receipt["source"]["ref"] = "0" * 40
    tampered = tmp_path / "method-source.json"
    tampered.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(validator, "METHOD_SOURCE_RECEIPT", tampered)

    assert any(
        "method source ref" in finding
        for finding in validator.validate_method_source(validator.METHOD_SOURCE_RECEIPT)
    )


def test_method_claim_text_and_schema_tampering_are_rejected(tmp_path: Path) -> None:
    receipt = json.loads(validator.METHOD_SOURCE_RECEIPT.read_text(encoding="utf-8"))
    receipt["schema_version"] = 999
    receipt["public_claims"] = [receipt["public_claims"][0]] * 6
    receipt["public_claims"][0]["claim"] = "SENSE is clinically validated."
    tampered = tmp_path / "method-source.json"
    tampered.write_text(json.dumps(receipt), encoding="utf-8")

    findings = validator.validate_method_source(tampered)
    assert any("schema_version" in finding for finding in findings)
    assert any("approved public claim map" in finding for finding in findings)
    assert any("claim ids must be unique" in finding for finding in findings)

    receipt["schema_version"] = True
    boolean_schema = tmp_path / "boolean-schema.json"
    boolean_schema.write_text(json.dumps(receipt), encoding="utf-8")
    assert any(
        "schema_version" in finding
        for finding in validator.validate_method_source(boolean_schema)
    )


def test_canonical_drift_is_rejected(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    index = root / "index.html"
    index.write_text(
        index.read_text(encoding="utf-8").replace(
            "https://thebridgemethod.net/", "https://www.thebridgemethod.net/", 1
        ),
        encoding="utf-8",
    )
    assert any("canonical" in finding for finding in validator.validate_site(root))


def test_fake_or_stale_favicon_is_rejected(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    index = root / "index.html"
    index.write_text(
        index.read_text(encoding="utf-8").replace(
            "favicon-bridge-d1573dd1a5af.svg", "favicon-bridge-deadbeef0000.svg"
        ),
        encoding="utf-8",
    )
    assert any("favicon" in finding for finding in validator.validate_site(root))


def test_404_favicon_drift_is_rejected(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    not_found = root / "404.html"
    not_found.write_text(
        not_found.read_text(encoding="utf-8").replace(
            "favicon-bridge-d1573dd1a5af.svg", "favicon-bridge-deadbeef0000.svg"
        ),
        encoding="utf-8",
    )
    assert any(
        "404" in finding and "favicon" in finding
        for finding in validator.validate_site(root)
    )


def test_missing_fragment_target_is_rejected(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    index = root / "index.html"
    index.write_text(
        index.read_text(encoding="utf-8").replace('href="#method"', 'href="#attic"', 1),
        encoding="utf-8",
    )
    assert any(
        "fragment target" in finding for finding in validator.validate_site(root)
    )


def test_missing_404_fragment_target_is_rejected(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    not_found = root / "404.html"
    not_found.write_text(
        not_found.read_text(encoding="utf-8").replace(
            'href="#main"', 'href="#gone"', 1
        ),
        encoding="utf-8",
    )
    assert any(
        "404 fragment target" in finding for finding in validator.validate_site(root)
    )


def test_design_token_drift_is_rejected(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    styles = root / "styles.css"
    styles.write_text(
        styles.read_text(encoding="utf-8").replace(
            "--paper: #f7f8f4", "--paper: #000000"
        ),
        encoding="utf-8",
    )
    assert any("--paper" in finding for finding in validator.validate_site(root))


def test_design_tokens_cannot_be_overridden_or_nested(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    styles = root / "styles.css"
    styles.write_text(
        styles.read_text(encoding="utf-8") + "\nbody { --paper: #000000; }\n",
        encoding="utf-8",
    )
    assert any("redeclared" in finding for finding in validator.validate_site(root))

    nested_root = copy_site(tmp_path / "nested")
    nested_styles = nested_root / "styles.css"
    source = nested_styles.read_text(encoding="utf-8")
    start = source.index(":root {")
    end = source.index("\n}", start)
    body = source[start + len(":root {") : end]
    nested_styles.write_text(
        source[:start]
        + ":root {\n  @media print {"
        + body
        + "\n  }\n}"
        + source[end + 2 :],
        encoding="utf-8",
    )
    assert any(
        "root value" in finding for finding in validator.validate_site(nested_root)
    )


def test_security_header_removal_is_rejected(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    headers = root / "_headers"
    headers.write_text(
        headers.read_text(encoding="utf-8").replace("X-Frame-Options: DENY", ""),
        encoding="utf-8",
    )
    assert any(
        "x-frame-options" in finding for finding in validator.validate_site(root)
    )


def test_commented_security_headers_do_not_count(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    headers = root / "_headers"
    source = headers.read_text(encoding="utf-8")
    headers.write_text(
        "\n".join(
            f"  # {line.strip()}"
            if ":" in line and "Cache-Control" not in line
            else line
            for line in source.splitlines()
        ),
        encoding="utf-8",
    )
    assert any("global" in finding for finding in validator.validate_site(root))


def test_redirect_targets_and_statuses_are_exact(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    redirects = root / "_redirects"
    redirects.write_text(
        redirects.read_text(encoding="utf-8").replace(
            "/#method 301", "/missing 301", 1
        ),
        encoding="utf-8",
    )
    assert any(
        "legacy route map" in finding for finding in validator.validate_site(root)
    )


def test_duplicate_redirect_sources_are_rejected(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    redirects = root / "_redirects"
    redirects.write_text(
        "/about /missing 301\n" + redirects.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    assert any(
        "duplicate source" in finding for finding in validator.validate_site(root)
    )


def test_duplicate_and_detached_security_headers_are_rejected(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    headers = root / "_headers"
    source = headers.read_text(encoding="utf-8")
    headers.write_text(
        "/*\n  X-Frame-Options: SAMEORIGIN\n" + source,
        encoding="utf-8",
    )
    findings = validator.validate_site(root)
    assert any("duplicate rule block" in finding for finding in findings)

    detached_root = copy_site(tmp_path / "detached")
    detached_headers = detached_root / "_headers"
    detached_headers.write_text(
        detached_headers.read_text(encoding="utf-8")
        + "\n/\n  ! Content-Security-Policy\n  ! X-Frame-Options\n",
        encoding="utf-8",
    )
    findings = validator.validate_site(detached_root)
    assert any("detach directives are forbidden" in finding for finding in findings)


def test_global_cache_rule_is_limited_to_no_transform(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    headers = root / "_headers"
    headers.write_text(
        headers.read_text(encoding="utf-8").replace(
            "  Cache-Control: no-transform",
            "  Cache-Control: public, max-age=0, must-revalidate, no-transform",
        ),
        encoding="utf-8",
    )
    assert any(
        "global Cache-Control policy must equal no-transform" in finding
        for finding in validator.validate_site(root)
    )


def test_overlapping_header_rule_is_rejected(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    headers = root / "_headers"
    headers.write_text(
        headers.read_text(encoding="utf-8")
        + "\n/fonts/inter-latin-variable.woff2\n  Cache-Control: public, max-age=0\n",
        encoding="utf-8",
    )
    assert any("rule patterns" in finding for finding in validator.validate_site(root))


def test_nonglobal_header_security_override_is_rejected(tmp_path: Path) -> None:
    root = copy_site(tmp_path)
    headers = root / "_headers"
    headers.write_text(
        headers.read_text(encoding="utf-8").replace(
            "/\n  Cache-Control: public, max-age=0, must-revalidate",
            "/\n  Cache-Control: public, max-age=0, must-revalidate\n"
            "  Referrer-Policy: unsafe-url",
            1,
        ),
        encoding="utf-8",
    )
    assert any(
        "must contain only Cache-Control" in finding
        for finding in validator.validate_site(root)
    )
