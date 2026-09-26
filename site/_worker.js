const PRESENTATION_ASSET_PATHS = new Set([
  "/social-bridge-56d23c0b80a4.png",
  "/apple-touch-icon-8aba0aa9e2bb.png",
  "/favicon-bridge-3c832bab8d39.png",
  "/icon-bridge-49892708a4a8.png",
]);

const CANONICAL_HOST = "thebridgemethod.net";
const ALIAS_HOSTS = new Set([
  "www.thebridgemethod.net",
  "the-bridge-method.pages.dev",
]);

function protectHtml(response) {
  if (!response.headers.get("content-type")?.includes("text/html")) {
    return response;
  }
  const cacheControl = response.headers.get("cache-control") || "";
  if (cacheControl.includes("no-transform")) {
    return response;
  }
  const headers = new Headers(response.headers);
  headers.set(
    "Cache-Control",
    cacheControl ? `${cacheControl}, no-transform` : "no-transform",
  );
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (ALIAS_HOSTS.has(url.hostname)) {
      url.protocol = "https:";
      url.hostname = CANONICAL_HOST;
      url.port = "";
      return new Response(null, {
        status: 301,
        headers: {
          Location: url.toString(),
          "Cache-Control": "public, max-age=3600",
          "Content-Security-Policy":
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none';",
          "Referrer-Policy": "strict-origin-when-cross-origin",
          "Strict-Transport-Security":
            "max-age=31536000; includeSubDomains; preload",
          "X-Content-Type-Options": "nosniff",
        },
      });
    }
    const response = await env.ASSETS.fetch(request);
    if (response.status === 200 && PRESENTATION_ASSET_PATHS.has(url.pathname)) {
      const headers = new Headers(response.headers);
      headers.set(
        "Cache-Control",
        "public, max-age=31536000, immutable, no-transform",
      );
      headers.set("X-Content-Type-Options", "nosniff");
      headers.delete("Content-Disposition");
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    }
    return protectHtml(response);
  },
};
