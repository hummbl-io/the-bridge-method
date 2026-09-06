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
