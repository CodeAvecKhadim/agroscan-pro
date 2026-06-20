/* idb.js — IndexedDB agroscan-offline v1 */
(function (global) {
  const DB_NAME = 'agroscan-offline';
  const DB_VERSION = 1;
  let _db = null;

  function openDB() {
    if (_db) return Promise.resolve(_db);
    return new Promise(function (resolve, reject) {
      var req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = function (e) {
        var db = e.target.result;
        if (!db.objectStoreNames.contains('parcelles'))
          db.createObjectStore('parcelles', { keyPath: 'id' });
        if (!db.objectStoreNames.contains('analyses_cache'))
          db.createObjectStore('analyses_cache', { keyPath: 'parcelle_id' });
        if (!db.objectStoreNames.contains('sync_queue'))
          db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
      };
      req.onsuccess = function (e) { _db = e.target.result; resolve(_db); };
      req.onerror = function (e) { reject(e.target.error); };
    });
  }

  function txGet(store, key) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var req = db.transaction(store, 'readonly').objectStore(store).get(key);
        req.onsuccess = function (e) { resolve(e.target.result); };
        req.onerror = function (e) { reject(e.target.error); };
      });
    });
  }

  function txGetAll(store) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var req = db.transaction(store, 'readonly').objectStore(store).getAll();
        req.onsuccess = function (e) { resolve(e.target.result); };
        req.onerror = function (e) { reject(e.target.error); };
      });
    });
  }

  function txPut(store, value) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var req = db.transaction(store, 'readwrite').objectStore(store).put(value);
        req.onsuccess = function (e) { resolve(e.target.result); };
        req.onerror = function (e) { reject(e.target.error); };
      });
    });
  }

  function txAdd(store, value) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var req = db.transaction(store, 'readwrite').objectStore(store).add(value);
        req.onsuccess = function (e) { resolve(e.target.result); };
        req.onerror = function (e) { reject(e.target.error); };
      });
    });
  }

  function txDelete(store, key) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var req = db.transaction(store, 'readwrite').objectStore(store).delete(key);
        req.onsuccess = function (e) { resolve(e.target.result); };
        req.onerror = function (e) { reject(e.target.error); };
      });
    });
  }

  /* ── parcelles ─────────────────────────────────────────────────────────── */
  function saveParcelles(list) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var t = db.transaction('parcelles', 'readwrite');
        var s = t.objectStore('parcelles');
        list.forEach(function (p) { s.put(p); });
        t.oncomplete = function () { resolve(); };
        t.onerror = function (e) { reject(e.target.error); };
      });
    });
  }

  function getParcelles() { return txGetAll('parcelles'); }

  /* ── analyses_cache ────────────────────────────────────────────────────── */
  function saveAnalyse(data) {
    /* data must have parcelle_id */
    var entry = Object.assign({}, data, { cached_at: new Date().toISOString() });
    return txPut('analyses_cache', entry);
  }

  function getAnalyse(parcelleId) { return txGet('analyses_cache', parcelleId); }

  /* ── sync_queue ────────────────────────────────────────────────────────── */
  function addToQueue(url, method, body) {
    return txAdd('sync_queue', {
      url: url,
      method: method,
      body: body,
      created_at: new Date().toISOString(),
      retry_count: 0,
    });
  }

  function getQueue() { return txGetAll('sync_queue'); }

  function removeFromQueue(id) { return txDelete('sync_queue', id); }

  function clearQueue() {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var req = db.transaction('sync_queue', 'readwrite').objectStore('sync_queue').clear();
        req.onsuccess = function () { resolve(); };
        req.onerror = function (e) { reject(e.target.error); };
      });
    });
  }

  global.IDB = {
    saveParcelles: saveParcelles,
    getParcelles: getParcelles,
    saveAnalyse: saveAnalyse,
    getAnalyse: getAnalyse,
    addToQueue: addToQueue,
    getQueue: getQueue,
    removeFromQueue: removeFromQueue,
    clearQueue: clearQueue,
  };
})(window);
