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
    return protectHtml(await env.ASSETS.fetch(request));
  },
};
