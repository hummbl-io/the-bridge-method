import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import test from "node:test";

import worker from "../site/_worker.js";

test("www redirects to the apex with path and query intact", async () => {
  const response = await worker.fetch(
    new Request("https://www.thebridgemethod.net/proof/path?source=test"),
    { ASSETS: { fetch: () => assert.fail("alias request reached assets") } },
  );
  assert.equal(response.status, 301);
  assert.equal(
    response.headers.get("location"),
    "https://thebridgemethod.net/proof/path?source=test",
  );
  assert.equal(response.headers.get("x-content-type-options"), "nosniff");
  assert.match(
    response.headers.get("content-security-policy"),
    /default-src 'none'/,
  );
});

test("the Pages hostname also canonicalizes", async () => {
  const response = await worker.fetch(
    new Request("https://the-bridge-method.pages.dev/build?from=pages"),
    { ASSETS: { fetch: () => assert.fail("alias request reached assets") } },
  );
  assert.equal(response.status, 301);
  assert.equal(
    response.headers.get("location"),
    "https://thebridgemethod.net/build?from=pages",
  );
});

test("apex requests pass through to the Pages asset service", async () => {
  const request = new Request("https://thebridgemethod.net/styles.css?v=1");
  let observed;
  const expected = new Response("asset", { status: 200 });
  const response = await worker.fetch(request, {
    ASSETS: {
      fetch(received) {
        observed = received;
        return expected;
      },
    },
  });
  assert.equal(observed, request);
  assert.equal(response, expected);
});

test("HTML fallbacks receive no-transform before leaving the Worker", async () => {
  const response = await worker.fetch(
    new Request("https://thebridgemethod.net/missing"),
    {
      ASSETS: {
        fetch: () =>
          new Response("missing", {
            status: 404,
            headers: {
              "Content-Type": "text/html; charset=utf-8",
              "Cache-Control": "no-store",
            },
          }),
      },
    },
  );
  assert.equal(response.status, 404);
  assert.equal(response.headers.get("cache-control"), "no-store, no-transform");
  assert.equal(await response.text(), "missing");
});

test("reviewed PNG assets preserve bytes and immutable caching", async () => {
  const manifest = JSON.parse(
    readFileSync(new URL("../presentation/manifest.json", import.meta.url)),
  );
  const config = JSON.parse(
    readFileSync(new URL("../presentation/config.json", import.meta.url)),
  );
  for (const asset of manifest.assets) {
    const path = asset.path.replace(/^site/, "");
    const bytes = readFileSync(new URL(`../${asset.path}`, import.meta.url));
    for (const status of [200, 404]) {
      const response = await worker.fetch(
        new Request(`https://${config.host}${path}`),
        {
          ASSETS: {
            async fetch() {
              return new Response(status === 200 ? bytes : "missing", {
                status,
                headers: {
                  "Content-Type": status === 200 ? "image/png" : "text/html",
                  "Cache-Control":
                    status === 200 ? "upstream" : "no-store, no-transform",
                },
              });
            },
          },
        },
      );
      assert.equal(response.status, status);
      if (status === 200) {
        assert.equal(response.headers.get("Content-Type"), "image/png");
        assert.equal(
          response.headers.get("Cache-Control"),
          "public, max-age=31536000, immutable, no-transform",
        );
        assert.deepEqual(Buffer.from(await response.arrayBuffer()), bytes);
      } else {
        assert.equal(
          response.headers.get("Cache-Control"),
          "no-store, no-transform",
        );
      }
    }
  }
});
