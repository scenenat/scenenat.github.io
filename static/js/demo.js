// Mounts the live SceneNAT demo.
//
// The demo is served by local_server.py on the GPU box, so this page only ever
// points at it -- nothing about the demo is vendored here.
//
// That server speaks plain HTTP, and github.io is HSTS-preloaded, so for almost
// every visitor the browser will refuse to frame it as mixed content. Rather
// than render a box that silently stays blank, detect the case up front and
// offer the demo as a link instead -- a new tab is a separate navigation and is
// not subject to the mixed-content rule. Point data-src at an HTTPS origin and
// the iframe path takes over with no other change.
(function mountDemo() {
  const host = document.getElementById('demo-frame');
  if (!host) return;

  const src = host.dataset.src;
  if (!src) return;

  const mixedContent = location.protocol === 'https:' && src.startsWith('http:');

  if (mixedContent) {
    host.classList.add('is-cta');

    const cta = document.createElement('div');
    cta.className = 'demo-cta';

    const blurb = document.createElement('p');
    blurb.textContent =
      'The demo server runs over plain HTTP, which this HTTPS page is not ' +
      'allowed to embed. It opens fine in its own tab.';

    const link = document.createElement('a');
    link.className = 'demo-launch';
    link.href = src;
    link.target = '_blank';
    link.rel = 'noopener';
    link.textContent = 'Launch the live demo';

    cta.appendChild(blurb);
    cta.appendChild(link);
    host.replaceChildren(cta);
    return;
  }

  const frame = document.createElement('iframe');
  frame.src = src;
  frame.title = 'SceneNAT interactive demo';
  frame.loading = 'lazy';
  frame.allow = 'fullscreen';
  host.replaceChildren(frame);
})();
