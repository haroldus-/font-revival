// Published pages retain exact SVG paths in gzip payloads to keep the complete
// historical gallery within the hosting allowance. No network request is needed
// for decompression; the SVG download remains a fallback for older browsers.
window.revivalArtworkReady = Promise.all(
  [...document.querySelectorAll('svg[data-icon-format] script[data-packed-svg]')].map(async payload => {
    if (!('DecompressionStream' in window)) {
      const fallback = payload.parentElement.querySelector('image[data-fallback-href]');
      fallback.setAttribute('href', fallback.dataset.fallbackHref);
      return;
    }
    const bytes = Uint8Array.from(atob(payload.textContent.trim()), character => character.charCodeAt(0));
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
    const artwork = await new Response(stream).text();
    payload.parentElement.innerHTML = artwork;
  })
);
