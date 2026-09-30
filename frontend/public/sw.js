// Kestrel Institutional Trading Platform - Service Worker (Offline Cache & PWA)
const CACHE_NAME = 'kestrel-v4-cache';
const PRECACHE_URLS = [
  '/',
  '/dashboard',
  '/analytics',
  '/copier',
  '/backtest',
  '/license',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // Network first with offline cache fallback for navigation requests
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(event.request) || caches.match('/dashboard');
      })
    );
    return;
  }

  // Stale-while-revalidate for static assets
  if (event.request.destination === 'style' || event.request.destination === 'script' || event.request.destination === 'image') {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        const fetchPromise = fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
          }
          return networkResponse;
        }).catch(() => cachedResponse);
        return cachedResponse || fetchPromise;
      })
    );
    return;
  }

  // Default network fetch
  event.respondWith(fetch(event.request));
});
