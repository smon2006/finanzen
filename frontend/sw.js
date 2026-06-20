const CACHE_NAME = 'finanzen-cache-v1';

const urlsToCache = [
  './',
  './index.html',
  './login.html',
  './signup.html',
  './dashboard.html',
  './style.css',
  './manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
  );
});