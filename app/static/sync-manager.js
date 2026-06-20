/* sync-manager.js — File d'attente hors-ligne AgroScan */
(function () {
  async function processSyncQueue() {
    if (!navigator.onLine) return 0;
    if (!window.IDB) return 0;

    var queue;
    try { queue = await IDB.getQueue(); } catch (e) { return 0; }
    if (!queue.length) return 0;

    var token = localStorage.getItem('agro_token') || localStorage.getItem('token') || '';
    var processed = 0;

    for (var i = 0; i < queue.length; i++) {
      var item = queue[i];
      try {
        var resp = await fetch(item.url, {
          method: item.method,
          headers: Object.assign(
            { 'Content-Type': 'application/json' },
            token ? { Authorization: 'Bearer ' + token } : {}
          ),
          body: item.body || undefined,
        });
        if (resp.ok) {
          await IDB.removeFromQueue(item.id);
          processed++;
        }
      } catch (e) {
        /* keep in queue, retry next time */
      }
    }

    if (processed > 0) {
      window.dispatchEvent(
        new CustomEvent('agroscan-sync-done', { detail: { processed: processed } })
      );
    }
    return processed;
  }

  async function registerBackgroundSync() {
    if (!('serviceWorker' in navigator)) return;
    try {
      var reg = await navigator.serviceWorker.ready;
      if ('sync' in reg) {
        await reg.sync.register('agroscan-sync-queue');
      }
    } catch (e) { /* Background Sync not supported */ }
  }

  /* retour en ligne → traiter la file */
  window.addEventListener('online', async function () {
    var count = await processSyncQueue();
    if (count > 0) {
      var msg = '✅ ' + count + ' action' + (count > 1 ? 's' : '') +
                ' synchronisée' + (count > 1 ? 's' : '') + ' avec le serveur';
      if (typeof toast === 'function') toast(msg);
      /* rafraîchir la liste des parcelles si disponible */
      if (typeof loadParcelles === 'function') setTimeout(loadParcelles, 600);
      if (typeof chargerParcelles === 'function') setTimeout(chargerParcelles, 600);
    }
  });

  /* message depuis le SW (Background Sync) */
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', async function (e) {
      if (e.data && e.data.type === 'TRIGGER_SYNC') {
        await processSyncQueue();
      }
    });
  }

  /* traiter au chargement si déjà en ligne */
  window.addEventListener('load', function () {
    if (navigator.onLine) processSyncQueue();
  });

  window.AgroSync = {
    processSyncQueue: processSyncQueue,
    registerBackgroundSync: registerBackgroundSync,
  };
})();
