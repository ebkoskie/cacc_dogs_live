/* CACC Dogs service worker: push notifications only.
 *
 * Registered by the dashboard (templates/index.html) only when a visitor turns
 * notifications on. It deliberately has NO fetch handler and caches nothing:
 * every request goes to the network exactly as without a worker (offline
 * support is a later release, which will add caching and a kill switch).
 * tests/test_sw_js.py runs this file under node and pins that.
 *
 * Payload (src/push.py): {"v":1,"n":[{"t":title,"b":body,"g":tag,"u":url}]}.
 * Each item is one notification; tags make a repeat replace the earlier one.
 */

const SW_FALLBACK = {
  t: 'CACC Dogs',
  b: 'There is news about the dogs. Tap to see it.',
  g: 'cacc-news',
  u: './?pn=fallback',
};
const SW_ICON = 'assets/icons/icon-192.png';
// Pages that may hold unsent input: a notification tap never navigates them.
const SW_KEEP_PAGES = /\/(upload|feedback)(\.html)?$/;

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

function swText(value, max) {
  return typeof value === 'string' ? value.slice(0, max) : '';
}

// The payload's items, validated; one generic item on bad data (browsers
// penalize a push that shows nothing).
function swItems(data) {
  let payload = null;
  try {
    payload = data ? data.json() : null;
  } catch (e) {
    payload = null;
  }
  const items = payload && payload.v === 1 && Array.isArray(payload.n) ? payload.n : [];
  const good = items
    .filter((it) => it && typeof it === 'object' && swText(it.t, 200))
    .slice(0, 6)
    .map((it) => ({
      t: swText(it.t, 200),
      b: swText(it.b, 400),
      g: swText(it.g, 64) || SW_FALLBACK.g,
      u: swText(it.u, 300) || SW_FALLBACK.u,
    }));
  return good.length ? good : [SW_FALLBACK];
}

self.addEventListener('push', (event) => {
  const items = swItems(event.data);
  event.waitUntil(
    Promise.all(
      items.map((it) =>
        self.registration.showNotification(it.t, {
          body: it.b,
          tag: it.g,
          icon: SW_ICON,
          badge: SW_ICON,
          data: { u: it.u },
        })
      )
    )
  );
});

// Same-origin URL for a notification's link, or the dashboard.
function swTargetUrl(raw) {
  const base = self.registration.scope;
  try {
    const url = new URL(raw || './', base);
    if (url.origin === new URL(base).origin) return url.href;
  } catch (e) {
    /* fall through */
  }
  return new URL('./', base).href;
}

function swIsDashboard(client, scope) {
  try {
    const path = new URL(client.url).pathname;
    const root = new URL(scope).pathname;
    if (SW_KEEP_PAGES.test(path)) return false;
    return path === root || path === root + 'index.html';
  } catch (e) {
    return false;
  }
}

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const target = swTargetUrl(event.notification.data && event.notification.data.u);
  event.waitUntil(
    (async () => {
      const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      const dash = all.find((c) => swIsDashboard(c, self.registration.scope));
      if (dash) {
        try {
          const focused = await dash.focus();
          const moved = await (focused || dash).navigate(target);
          if (moved) return;
        } catch (e) {
          /* navigate() rejects for an uncontrolled client: open a window instead */
        }
      }
      await self.clients.openWindow(target);
    })()
  );
});
