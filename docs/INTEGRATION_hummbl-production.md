# Integration with hummbl-production

**Date:** 2026-09-09
**Status:** Active

---

## What this repo is

`hummbl-io/the-bridge-method` owns the public `thebridgemethod.net` surface — the coaching method surface. Source lives in `site/` and is deployed to Cloudflare Pages project `the-bridge-method`.

## Relationship to hummbl-production

`hummbl-production` is the primary product repository (`hummbl.io`) and the estate authority. It holds:

1. **Implementation receipt** — `cloudflare/evidence/the-bridge-method-305a608.json` binds this repo's commit `305a608894d19999887ee10a37989e8d75374707` and all 18 deployable-tree file hashes to Pages deployment `81da800d-67b3-4fc0-ac5e-983238d5d66b`. The source also binds its published method claims to six exact coaching-canon blobs.

2. **Estate registry** — `cloudflare/estate-registry.json` and `docs/strategy/estate/REGISTRY.md` record this repo as the repository owner for `thebridgemethod.net`, with proposed classification CANONICAL and constellation role `coaching_method_surface`.

3. **Domain constellation** — `cloudflare/domain-constellation.json` declares the strategic ownership, purpose, design status, and cross-domain relationships. Registrar is GoDaddy; DNS provider is Cloudflare.

4. **Operations observation** — `cloudflare/operations.json` records the authenticated Cloudflare zone state.

## Cross-domain links

| This domain | Links to | Relationship |
|---|---|---|
| `thebridgemethod.net` | `reubenbowlby.com` | primary_personal |
| `thebridgemethod.net` | `hummbl.io` | primary_product |

## Deployment surface

| Surface | Pages project | Deploy root | Workflow |
|---|---|---|---|
| `thebridgemethod.net` | `the-bridge-method` | `site/` | `.github/workflows/site.yml` |

## What hummbl-production validates about this repo

- The constellation validator checks that the observed Cloudflare zone state matches the declared constellation, including the GoDaddy registrar evidence.
- The estate registry validator checks that the registry agrees with the constellation, surfaces, and linked implementation receipt.
- The implementation receipt is validated for provider reconciliation and coaching-canon blob binding without re-authenticating the private repository.

## What this repo should do

- Maintain the `site/` deployable tree and `.github/workflows/site.yml` deployment workflow.
- Preserve the shared HUMMBL design tokens (`hummbl-global-light-v1`).
- Keep cross-domain links consistent with the constellation declared in hummbl-production.
- Do not present candidate or unresolved material as current. Do not invent credentials, clinical claims, or guaranteed outcomes.
