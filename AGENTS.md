# AGENTS.md — The Bridge Method

This repository owns the public thebridgemethod.net surface.

## Content authority

The canonical method source is the approved coaching-system package in the
private hummbl-io/coaching repository, adopted July 28, 2026. Public copy may
describe its governing loop, 13D, SENSE, Physical Task Bridge, Client as Agent,
human-flourishing aim, session architecture, and explicit scope boundaries.

Do not present candidate or unresolved material as current. Do not invent
credentials, services, testimonials, clinical claims, validated-outcome claims,
exercise prescriptions, or guarantees. Coaching content must not diagnose,
treat, medically clear, or replace qualified professional judgment.

## Surface contract

- Keep thebridgemethod.net canonical. Every hostname alias must redirect with
  the path and query intact.
- Keep unknown routes as real 404 responses.
- Preserve the shared HUMMBL design tokens enforced by
  scripts/validate_site.py.
- Keep public fonts and runtime assets local; do not add third-party runtime
  scripts, trackers, or analytics beacons.
- Never add mailto links.
- Validate source, tests, Worker behavior, and formatting before push.
- Land consequential changes through signed Conventional Commit PRs.

## Approval authority

Reuben is the sole owner and final approval authority. Do not configure or
suggest branch protection that requires approval from hummbl-agent, another
agent account, or any additional human. Automated checks may gate correctness;
they do not add an approver above or beside Reuben.
