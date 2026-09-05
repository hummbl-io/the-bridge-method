# The Bridge Method

[thebridgemethod.net](https://thebridgemethod.net) is the governed public
doorway into Reuben Bowlby's documented coaching system.

The method connects a person's intent to an observable task, present-state
evidence, an authorized next action, and shared review. Its public definition is
grounded in the approved coaching canon in hummbl-io/coaching, including 13D,
SENSE, the Physical Task Bridge, and Client as Agent.

The exact upstream commit, source-file hashes, audience declaration, and public
claim map are recorded in [evidence/method-source.json](evidence/method-source.json).

## Public surface

The complete Cloudflare Pages artifact lives in [site/](site/). It has one
canonical route, a governed 404, a small route map, self-hosted fonts, and an
edge worker that canonicalizes every alias while preserving the path and query
string.

| Surface                                            | Relationship                      |
| -------------------------------------------------- | --------------------------------- |
| [thebridgemethod.net](https://thebridgemethod.net) | Public coaching-method surface    |
| [reubenbowlby.com](https://reubenbowlby.com)       | Method owner and current practice |
| [hummbl.io](https://hummbl.io)                     | Governed system and public work   |
| [hummbl.house](https://hummbl.house)               | Company home behind the work      |
| [rpbx.net](https://rpbx.net)                       | Reuben's heritage identity        |

## Content authority

The public method follows the coaching canon adopted on July 28, 2026:

> govern → observe → prepare → train → adapt → record → review

It describes coaching process and boundaries. It does not diagnose, treat,
medically clear, automatically assign exercise, score a person's worth, or
guarantee health or performance outcomes.

## Invariants

- https://thebridgemethod.net/ is canonical.
- www.thebridgemethod.net and the-bridge-method.pages.dev return 301 to the
  exact apex path and query.
- Unknown paths return the source-controlled 404.html with status 404.
- HTML carries no-transform; static assets use explicit cache policies.
- Shared HUMMBL paper, forest, green, and mint tokens are declared once and may
  not be overridden.
- Every font is self-hosted and its OFL license ships beside it.
- Public method claims stay within the approved coaching canon and its stated
  evidence status.
- The site links to Reuben, HUMMBL, HUMMBL House, and RPBx.

Run the source and edge contract locally:

    python scripts/validate_site.py
    python -m pytest tests -q
    node --test tests/test_worker.mjs

Merges to main deploy site/ to the the-bridge-method Cloudflare Pages project
and then run the live route and header audit.

## Typeface licenses

The site self-hosts Inter, JetBrains Mono, and Crimson Pro. Each is distributed
under the SIL Open Font License 1.1; the corresponding license texts are in
[site/fonts/](site/fonts/).
