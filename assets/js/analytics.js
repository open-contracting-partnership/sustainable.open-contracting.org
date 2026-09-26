// Google Analytics, whose ID is the script element's data-id.
window.dataLayer = window.dataLayer || [];
function gtag() {
  // biome-ignore lint/complexity/noArguments: gtag.js expects the arguments object.
  window.dataLayer.push(arguments);
}
gtag("js", new Date());
gtag("config", document.currentScript.dataset.id);
