/* MayoMandi Service Worker — App Shell caching */
const CACHE_NAME = "mayomandi-v1";
const API_CACHE = "mayomandi-api-v1";

// App shell: core assets that must work offline
const CORE_ASSETS = [
  "/",
  "/index.html",
  "/manifest.json",
  "/src/index.css",
  "/src/main.js",
  "/src/assets/hero.png",
  "/favicon.svg",
  "/pwa-192.png",
  "/pwa-512.png",
  "/maskable-192.png",
  "/maskable-512.png",
];

// Assets cacheable at install time (fonts are CDN-origin, cache on demand)
const FONT_CACHE = "mayomandi-fonts-v1";
const FONT_URLS = [
  "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Kalam:wght@400;700&family=Comic+Neue:wght@300;400;700&display=swap",
];

// Install: pre-cache app shell
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(CORE_ASSETS))
      .then(() => self.skipWaiting()),
  );
});

// Activate: clean old caches
self.addEventListener("activate", (event) => {
  const currentCaches = [CACHE_NAME, API_CACHE, FONT_CACHE];
  event.waitUntil(
    caches
      .keys()
      .then((names) =>
        Promise.all(
          names.map((name) => {
            if (!currentCaches.includes(name)) {
              return caches.delete(name);
            }
            return null;
          }),
        )
      )
      .then(() => self.clients.claim()),
  );
});

// Fetch: stale-while-revalidate for shell, network-first for API
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API requests — network first, cache GET responses only (Cache API doesn't support POST)
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/health")) {
    event.respondWith(
      fetch(event.request).then((response) => {
        // Only cache GET responses; POST requests must always hit the network
        if (event.request.method === "GET") {
          const cloned = response.clone();
          caches.open(API_CACHE).then((cache) => cache.put(event.request, cloned));
        }
        return response;
      }).catch(() => caches.match(event.request)),
    );
    return;
  }

  // Google Fonts — cache first
  if (url.origin === "https://fonts.googleapis.com" || url.origin === "https://fonts.gstatic.com") {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) {
          return cached;
        }
        return fetch(request).then((response) => {
          const cloned = response.clone();
          caches.open(FONT_CACHE).then((cache) => cache.put(request, cloned));
          return response;
        });
      }),
    );
    return;
  }

  // App shell & same-origin assets — cache first (stale-while-revalidate)
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) {
          // Fetch fresh in background and update cache
          fetch(request).then((response) => {
            if (response.ok) {
              caches.open(CACHE_NAME).then((cache) => cache.put(request, response.clone()));
            }
          }).catch(() => {});
          return cached;
        }
        return fetch(request).then((response) => {
          if (response.ok) {
            caches.open(CACHE_NAME).then((cache) => cache.put(request, response.clone()));
          }
          return response.clone();
        });
      }),
    );
    return;
  }

  // Default: network
  event.respondWith(fetch(request));
});
