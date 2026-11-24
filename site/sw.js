// Modo app: abre mesmo com sinal fraco ou sem internet, mostrando a última agenda baixada.
// Arquivos do site: tenta a internet primeiro (dados sempre frescos) e usa a cópia guardada se falhar.
// Bibliotecas do mapa (unpkg): usa a cópia guardada, porque não mudam.
const VERSAO = "mapa-leiloes-v2";
const BASICO = ["./", "index.html", "estilo.css", "app.js", "leiloes.js", "manifest.webmanifest",
  "icone-192.png", "icone-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(BASICO)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((nomes) => Promise.all(nomes.filter((n) => n !== VERSAO).map((n) => caches.delete(n))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  if (url.origin === location.origin) {
    e.respondWith(fetch(req, { cache: "no-cache" }).then((resp) => {
      if (resp.ok) { const copia = resp.clone(); caches.open(VERSAO).then((c) => c.put(req, copia)); }
      return resp;
    }).catch(() => caches.match(req, { ignoreSearch: true })
      .then((r) => r || caches.match("index.html"))));
    return;
  }

  if (url.hostname === "unpkg.com") {
    e.respondWith(caches.match(req).then((r) => r || fetch(req).then((resp) => {
      if (resp.ok) { const copia = resp.clone(); caches.open(VERSAO).then((c) => c.put(req, copia)); }
      return resp;
    })));
  }
  // Mapas (OpenStreetMap) e links externos: segue normal, sem guardar
});
