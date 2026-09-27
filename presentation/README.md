# The Bridge Method presentation assets

`card.html` is the editable HTML/SVG source for the 1200×630 social card.
The copy comes from the public homepage and retains its **human coaching**
role. The 32px favicon, 180px touch icon and 192px icon are local browser renders
of the existing `favicon-bridge-d1573dd1a5af.svg` mark on an opaque forest background.
The original SVG and wordmark remain in place. No photographic likeness,
synthetic product imagery, third-party runtime resource or tracker is introduced.

Fonts are the bundled Inter, Crimson Pro and JetBrains Mono files; their OFL
licenses remain under `site/fonts/`. Editable sources stay outside deployed
`site/`. The PNGs are content-addressed and their source/output hashes and browser
versions are recorded in `manifest.json`.

To revise deliberately with a local environment containing Playwright and Chrome
or Chromium:

```sh
python scripts/render_presentation.py --browser /path/to/chromium
```

Omit `--browser` to use Playwright's installed Chromium. Rendering is an optional
maintainer step, not a runtime or CI dependency. Rasterization may vary between
browser versions. Review the images, update metadata and exact cache routes to
the newly generated hashes, and run the website and worker tests before release.
Retain previously published content-addressed assets for existing shared links.
CI verifies source/output hashes, PNG sizes, metadata and same-origin paths using
the standard library. The 192px icon is a browser icon; no installable-app behavior
is claimed or configured.
