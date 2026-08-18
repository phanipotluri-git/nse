// NSE Risk Monitor — Service Worker v21
// NO shell pre-caching — HTML is always fetched fresh from network.
// On activate: wipe ALL previous caches so stale HTML never blocks updates.

self.addEventListener("install", e => {
  // Skip waiting immediately — no shell to pre-cache
  e.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", e => {
  e.waitUntil(
    // Delete every cache, including any that contain stale screener.html
    caches.keys()
      .then(keys => Promise.all(keys.map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);

  // CORS proxy URLs — network only, empty-object fallback (Risk Monitor live fetch)
  const live = ["query1.finance.yahoo.com","corsproxy.io","allorigins.win",
                "codetabs.com","thingproxy.freeboard.io","cors.sh"];
  if (live.some(h => url.hostname.includes(h))) {
    e.respondWith(fetch(e.request).catch(() =>
      new Response("{}", {headers:{"Content-Type":"application/json"}})
    ));
    return;
  }

  // risk_factors.json — network-first, cache as fallback for Risk Monitor offline
  if (url.pathname.endsWith("risk_factors.json")) {
    e.respondWith((async () => {
      const cache = await caches.open("nse-data-v1");
      const cacheKey = new Request(url.pathname);
      try {
        const res = await fetch(e.request);
        if (res.ok) {
          const body = await res.text();
          if (body && body.length > 1) {
            cache.put(cacheKey, new Response(body, {status:200, headers:{"Content-Type":"application/json"}}));
            return new Response(body, {status:200, headers:{"Content-Type":"application/json"}});
          }
        }
        return (await cache.match(cacheKey)) || res;
      } catch(_) {
        return (await cache.match(cacheKey)) ||
          new Response("{}", {status:200, headers:{"Content-Type":"application/json"}});
      }
    })());
    return;
  }

  // Everything else (HTML, JS, CSS, screener_results.json via relative path):
  // pass straight to network — no SW caching.
});
