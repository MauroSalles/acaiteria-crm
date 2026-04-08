const CACHE_NAME = 'acai-crm-v16';
const SYNC_QUEUE = 'acai-sync-queue';
const STATIC_ASSETS = [
  '/static/estilos.css',
  '/static/script.js',
  '/static/manifest.json',
  '/static/icon-192.svg',
  '/static/icon-512.svg',
  '/offline',
];

// Instalação — cacheia assets estáticos
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Ativação — limpa caches antigos + replay sync queue
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => _replayQueue().catch(() => {}))
  );
  self.clients.claim();
});

// Fetch — network first, fallback para cache, offline page as ultimate fallback
self.addEventListener('fetch', (event) => {
  // Ignorar requisições não-GET e API (sempre rede)
  if (event.request.method !== 'GET' || event.request.url.includes('/api/')) {
    // Para POST/PUT/DELETE em /api/ — enfileirar se offline
    if (event.request.method !== 'GET' && event.request.url.includes('/api/')) {
      event.respondWith(
        fetch(event.request.clone()).catch(() => {
          // Rede indisponível — salvar na fila de sync
          return event.request.clone().text().then((body) => {
            return _enqueueSync({
              url: event.request.url,
              method: event.request.method,
              headers: Object.fromEntries(event.request.headers.entries()),
              body: body,
              timestamp: Date.now(),
            }).then(() => {
              return new Response(
                JSON.stringify({ offline: true, msg: 'Salvo para envio quando online.' }),
                { status: 202, headers: { 'Content-Type': 'application/json' } }
              );
            });
          });
        })
      );
    }
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Só cachear respostas bem-sucedidas que não sejam redirects
        // e que não sejam a página de login (evita cachear login como '/')
        if (response.ok && !response.redirected
            && !event.request.url.includes('/login')) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => {
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;
          // Se é navegação HTML, mostrar página offline
          if (event.request.mode === 'navigate') {
            return caches.match('/offline');
          }
          return new Response('Offline', { status: 503, statusText: 'Offline' });
        });
      })
  );
});

// ==========================================================================
// OFFLINE SYNC QUEUE — IndexedDB-backed request queue
// ==========================================================================

function _openSyncDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(SYNC_QUEUE, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains('requests')) {
        db.createObjectStore('requests', { autoIncrement: true });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function _enqueueSync(entry) {
  return _openSyncDB().then((db) => {
    return new Promise((resolve, reject) => {
      const tx = db.transaction('requests', 'readwrite');
      tx.objectStore('requests').add(entry);
      tx.oncomplete = () => {
        // Registrar background sync se disponível
        if (self.registration && self.registration.sync) {
          self.registration.sync.register('replay-queue').catch(() => {});
        }
        resolve();
      };
      tx.onerror = () => reject(tx.error);
    });
  });
}

function _replayQueue() {
  return _openSyncDB().then((db) => {
    return new Promise((resolve, reject) => {
      const tx = db.transaction('requests', 'readonly');
      const store = tx.objectStore('requests');
      const all = store.getAll();
      const keys = store.getAllKeys();
      all.onsuccess = () => {
        resolve({ entries: all.result, keys: keys.result, db: db });
      };
      all.onerror = () => reject(all.error);
    });
  }).then(({ entries, keys, db }) => {
    if (!entries.length) return;
    return entries.reduce((chain, entry, i) => {
      return chain.then(() => {
        return fetch(entry.url, {
          method: entry.method,
          headers: entry.headers,
          body: entry.body || undefined,
        }).then((resp) => {
          if (resp.ok || resp.status < 500) {
            // Remove da fila após sucesso
            const del = db.transaction('requests', 'readwrite');
            del.objectStore('requests').delete(keys[i]);
            return new Promise((r) => { del.oncomplete = r; });
          }
        });
      });
    }, Promise.resolve());
  });
}

// Background Sync
self.addEventListener('sync', (event) => {
  if (event.tag === 'replay-queue') {
    event.waitUntil(_replayQueue());
  }
});

// Push Notifications (preparado para uso futuro)
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : { titulo: 'Combina Açaí', corpo: 'Nova notificação' };
  event.waitUntil(
    self.registration.showNotification(data.titulo || 'Combina Açaí CRM', {
      body: data.corpo || '',
      icon: '/static/icon-192.svg',
      badge: '/static/icon-192.svg',
      vibrate: [100, 50, 100],
      data: { url: data.url || '/' },
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(clients.openWindow(url));
});
