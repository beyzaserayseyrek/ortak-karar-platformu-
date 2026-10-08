// Never cache private pages, authentication or POST requests.
self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
self.addEventListener('fetch',event=>{
 if(event.request.method==='GET' && event.request.mode==='navigate'){
  event.respondWith(fetch(event.request).catch(()=>new Response('<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Müzakere · Çevrimdışı</title><h1>Bağlantı yok</h1><p>Oy ve katkı kaydetmek için tekrar internete bağlan. Hiçbir işlem çevrimdışı gönderilmiş sayılmaz.</p></html>',{headers:{'Content-Type':'text/html; charset=utf-8'}})));
 }
});
