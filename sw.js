// NSE Risk Monitor — Service Worker v17
const CACHE = "nse-risk-v18";
const SHELL = ["./", "./index.html", "./screener.html", "./manifest.json"];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  const live = ["query1.finance.yahoo.com","corsproxy.io","allorigins.win",
                "codetabs.com","thingproxy.freeboard.io","cors.sh"];
  if (live.some(h => url.hostname.includes(h))) {
    e.respondWith(fetch(e.request).catch(() => new Response("{}", {headers:{"Content-Type":"application/json"}})));
    return;
  }
  if (url.pathname.endsWith("risk_factors.json") || url.pathname.endsWith("screener_results.json")) {
    e.respondWith(
      caches.open(CACHE).then(async cache => {
        const cacheKey = new Request(url.pathname);
        const cached = await cache.match(cacheKey);
        try {
          const res = await fetch(e.request);
          if (res.ok) {
            // Read body as text — NEVER use res.clone() on Safari/WKWebView.
            // clone() produces a broken stream tee that empties the original body.
            const body = await res.text();
            const headers = {"Content-Type": "application/json"};
            cache.put(cacheKey, new Response(body, {status: 200, headers}));
            return new Response(body, {status: 200, headers});
          }
          return cached || res;
        } catch(_) {
          return cached || new Response('{"results":[]}', {
            status: 200,
            headers: {"Content-Type": "application/json"}
          });
        }
      })
    );
    return;
  }
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(res => {
      if (res.ok && url.origin === self.location.origin)
        caches.open(CACHE).then(c => c.put(e.request, res.clone()));
      return res;
    }))
  );
});
