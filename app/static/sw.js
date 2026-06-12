/**
 * AgroScan Pro — Service Worker
 * Cache-first pour assets statiques, network-first pour API.
 * Push notifications pour alertes satellite et activités en retard.
 */

const CACHE_NAME = 'agroscan-v1';
const CACHE_DURATION_MS = 24 * 60 * 60 * 1000; // 24h

// Assets à précacher au démarrage
const PRECACHE = [
  '/',
  '/app',
  '/mon-champ',
  '/static/i18n.js',
  '/static/i18n/fr.json',
  '/static/css/agroscan.css',
];

// ── Installation ──────────────────────────────────────────────────────────────

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

// ── Activation ────────────────────────────────────────────────────────────────

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// ── Fetch — stratégie mixte ───────────────────────────────────────────────────

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // API : network-first (pas de cache)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request).catch(() => new Response(
      JSON.stringify({detail: 'Hors ligne — données non disponibles.'}),
      {status: 503, headers: {'Content-Type': 'application/json'}}
    )));
    return;
  }

  // Assets statiques : cache-first
  if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/uploads/')) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }))
    );
    return;
  }

  // Pages HTML : network-first avec fallback cache
  event.respondWith(
    fetch(event.request)
      .then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request).then(cached => cached || caches.match('/app')))
  );
});

// ── Push Notifications ────────────────────────────────────────────────────────

self.addEventListener('push', event => {
  let data = { title: 'AgroScan Pro', body: 'Nouvelle notification', icon: '/static/icons/icon-192.png', tag: 'agroscan' };
  try {
    if (event.data) Object.assign(data, event.data.json());
  } catch (_) {}

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon || '/static/icons/icon-192.png',
      badge: '/static/icons/icon-192.png',
      tag: data.tag || 'agroscan',
      requireInteraction: data.urgent || false,
      data: { url: data.url || '/app' },
      actions: data.actions || [],
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data?.url || '/app';
  event.waitUntil(
    clients.matchAll({type: 'window'}).then(wins => {
      for (const win of wins) {
        if (win.url.includes(self.location.origin) && 'focus' in win) {
          win.navigate(url);
          return win.focus();
        }
      }
      return clients.openWindow(url);
    })
  );
});
