const CACHE_NAME = 'acai-crm-v13';
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

// Ativação — limpa caches antigos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch — network first, fallback para cache, offline page as ultimate fallback
self.addEventListener('fetch', (event) => {
  // Ignorar requisições não-GET e API (sempre rede)
  if (event.request.method !== 'GET' || event.request.url.includes('/api/')) {
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
