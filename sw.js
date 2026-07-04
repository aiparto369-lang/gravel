/* ==========================================================
   گراول (Gravel) — Service Worker
   © Mehdi Rezghi — https://t.me/Mehdirezghi
   نسخه را ربات گراول خودکار جلو می‌برد؛ دستی دست نزن.
   ========================================================== */

const VERSION = "v2";
const CACHE = "gravel-" + VERSION;

const PRECACHE = [
  "./",
  "./index.html",
  "./catalog.json",
  "./manifest.webmanifest",
  "./404.html",
  "./icon-192.png",
  "./icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  const cacheable =
    url.origin === location.origin ||
    url.hostname === "fonts.googleapis.com" ||
    url.hostname === "fonts.gstatic.com" ||
    url.hostname === "cdnjs.cloudflare.com";
  if (!cacheable) return;

  /* فهرست آموزش‌ها: اول شبکه (تا آموزش تازه فوری دیده شود)، اگر نبود از کش */
  if (url.pathname.endsWith("/catalog.json")) {
    event.respondWith(
      caches.open(CACHE).then(async (cache) => {
        try {
          const fresh = await fetch(req);
          if (fresh && fresh.status === 200) cache.put(req, fresh.clone());
          return fresh;
        } catch (e) {
          return (await cache.match(req)) || Response.error();
        }
      })
    );
    return;
  }

  /* بقیه: اول کش (سریع)، هم‌زمان نسخهٔ تازه گرفته و کش به‌روز می‌شود */
  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const cached = await cache.match(req);
      const network = fetch(req)
        .then((res) => {
          if (res && res.status === 200) cache.put(req, res.clone());
          return res;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
