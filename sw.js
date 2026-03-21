const CACHE_NAME = 'hakgun-v2';
const ASSETS = [
    './',
    './index.html',
    './style.css',
    './app.js',
    './api.js',
    './icon.png',
    './manifest.json'
];

self.addEventListener('install', (e) => {
    self.skipWaiting(); // 즉시 활성화
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
    );
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((keyList) => {
            return Promise.all(keyList.map((key) => {
                if (key !== CACHE_NAME) {
                    return caches.delete(key);
                }
            }));
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (e) => {
    // API 통신은 네트워크 우선, 나머지도 네트워크 우선(단, 실패 시 캐시)
    e.respondWith(
        fetch(e.request).catch(() => caches.match(e.request))
    );
});
