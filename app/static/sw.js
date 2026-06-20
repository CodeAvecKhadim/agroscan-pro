/**
 * AgroScan Pro — Service Worker v3
 * Scope : / (servi via /sw.js avec header Service-Worker-Allowed: /)
 * Stratégies :
 *   - Pages HTML terrain : network-first + fallback cache + offline.html
 *   - Assets statiques   : cache-first (stale-while-revalidate)
 *   - API GET cachables  : stale-while-revalidate 24h
 *   - API sensibles      : network-only (auth, billing, IA, satellite write)
 *   - Background Sync    : agroscan-sync-queue
 *   - Push notifications : implémentées
 */

const CACHE_NAME    = 'agroscan-v3';
const CACHE_API     = 'agroscan-api-v3';
const CACHE_24H_MS  = 24 * 60 * 60 * 1000;

// ── Pages terrain à précacher ─────────────────────────────────────────────────
const PRECACHE_PAGES = [
  '/',
  '/app',
  '/mon-champ',
  '/sante-cultures',
  '/meteo',
  '/activites',
  '/carte',
  '/photo',
  '/sante',
  '/offline',
];

// ── Assets statiques à précacher ──────────────────────────────────────────────
const PRECACHE_ASSETS = [
  '/static/i18n.js',
  '/static/i18n/fr.json',
  '/static/network-status.js',
  '/static/idb.js',
  '/static/sync-manager.js',
  '/static/css/agroscan.css',
  '/static/css/design-system.css',
  '/static/assets/favicon.png',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/assets/logo-emblem.svg',
  '/static/assets/logo-wordmark.svg',
  '/static/assets/polele-avatar.svg',
];

const PRECACHE_ALL = [...PRECACHE_PAGES, ...PRECACHE_ASSETS];

// ── Endpoints API cachables (GET lecture, données agricoles) ──────────────────
const CACHEABLE_API = [
  '/api/champ/parcelles',
  '/api/auth/me',
  '/api/billing/me',
  '/api/agronomie/cultures',
  '/api/app/activites',
  '/api/meteo/conditions',
  '/api/meteo/dashboard',
  '/api/meteo/alertes',
  '/api/ferme/activites',
  '/api/sante-cultures/analyses/',
];

// ── Endpoints jamais cachés (écriture, secrets, IA, paiements) ───────────────
const NEVER_CACHE = [
  '/api/auth/login',
  '/api/auth/logout',
  '/api/auth/register',
  '/api/billing/',
  '/api/credits/',
  '/api/ia/',
  '/api/analyse/',
  '/api/sante-cultures/analyser',
  '/api/satellite/',
  '/api/sante/precision/satellite',
  '/api/meteo/alertes/generer',
  '/api/meteo/planificateur/generer',
];

// ── Install ───────────────────────────────────────────────────────────────────

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE_ALL))
      .then(() => self.skipWaiting())
      .catch(err => console.warn('[SW] Précache partiel:', err))
  );
});

// ── Activate ──────────────────────────────────────────────────────────────────

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(k => k !== CACHE_NAME && k !== CACHE_API)
          .map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// ── Fetch ─────────────────────────────────────────────────────────────────────

self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // Ignorer non-GET et cross-origin (Sentinel Hub, Anthropic, Google Fonts…)
  if (req.method !== 'GET' || url.origin !== self.location.origin) return;

  const path = url.pathname;

  // Endpoints jamais cachés → network-only
  if (NEVER_CACHE.some(p => path.startsWith(p))) {
    event.respondWith(
      fetch(req).catch(() => new Response(
        JSON.stringify({ detail: 'Hors ligne — opération non disponible sans connexion.' }),
        { status: 503, headers: { 'Content-Type': 'application/json' } }
      ))
    );
    return;
  }

  // API GET cachables → stale-while-revalidate 24h
  if (path.startsWith('/api/') && CACHEABLE_API.some(p => path.startsWith(p))) {
    event.respondWith(staleWhileRevalidate(req, CACHE_API));
    return;
  }

  // API non listée → network-first, pas de cache
  if (path.startsWith('/api/')) {
    event.respondWith(
      fetch(req).catch(() => new Response(
        JSON.stringify({ detail: 'Hors ligne — données non disponibles.' }),
        { status: 503, headers: { 'Content-Type': 'application/json' } }
      ))
    );
    return;
  }

  // Assets statiques → cache-first
  if (path.startsWith('/static/') || path.startsWith('/uploads/')) {
    event.respondWith(cacheFirst(req));
    return;
  }

  // Pages HTML → network-first + fallback cache + offline.html
  event.respondWith(networkFirstPage(req));
});

// ── Stratégies ────────────────────────────────────────────────────────────────

async function cacheFirst(req) {
  const cached = await caches.match(req);
  if (cached) return cached;
  try {
    const response = await fetch(req);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(req, response.clone());
    }
    return response;
  } catch {
    return new Response('Asset indisponible hors ligne.', { status: 503 });
  }
}

async function staleWhileRevalidate(req, cacheName) {
  const cache  = await caches.open(cacheName);
  const cached = await cache.match(req);

  const fetchPromise = fetch(req).then(response => {
    if (response.ok) {
      const clone = response.clone();
      cache.put(req, clone);
    }
    return response;
  }).catch(() => null);

  if (cached) {
    // Mettre à jour en arrière-plan, retourner le cache immédiatement
    fetchPromise.catch(() => {});
    return cached;
  }

  // Pas de cache — attendre le réseau
  const response = await fetchPromise;
  if (response) return response;

  return new Response(
    JSON.stringify({ detail: 'Données non disponibles hors ligne.' }),
    { status: 503, headers: { 'Content-Type': 'application/json' } }
  );
}

async function networkFirstPage(req) {
  try {
    const response = await fetch(req);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(req, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(req);
    if (cached) return cached;

    // Fallback ultime : page offline
    const offline = await caches.match('/offline');
    return offline || new Response(
      '<h1>Hors ligne</h1><p><a href="/app">Retour</a></p>',
      { headers: { 'Content-Type': 'text/html' } }
    );
  }
}

// ── Push Notifications ────────────────────────────────────────────────────────

self.addEventListener('push', event => {
  let data = {
    title: 'AgroScan Pro',
    body:  'Nouvelle notification',
    icon:  '/static/icons/icon-192.png',
    tag:   'agroscan',
  };
  try {
    if (event.data) Object.assign(data, event.data.json());
  } catch (_) {}

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body:              data.body,
      icon:              data.icon || '/static/icons/icon-192.png',
      badge:             '/static/icons/icon-192.png',
      tag:               data.tag || 'agroscan',
      requireInteraction: data.urgent || false,
      data:              { url: data.url || '/app' },
      actions:           data.actions || [],
    })
  );
});

// ── Background Sync ───────────────────────────────────────────────────────────

self.addEventListener('sync', event => {
  if (event.tag === 'agroscan-sync-queue') {
    event.waitUntil(
      self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clients => {
        clients.forEach(client => client.postMessage({ type: 'TRIGGER_SYNC' }));
      })
    );
  }
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data?.url || '/app';
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(wins => {
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
