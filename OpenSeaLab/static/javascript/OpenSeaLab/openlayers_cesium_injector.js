//INJECTS CESIUM INTO A OPENLAYERS APPLICATION
(function() {
  const mode = window.location.href.match(/mode=([a-z0-9\-]+)\&?/i);
  const DIST = true;
  const isDev = mode && mode[1] === 'dev';
  window.IS_DEV = isDev;
  const cs = isDev ? 'CesiumUnminified/Cesium.js' : 'static/cesium-1.39/Build/Cesium/Cesium.js';
  const ol = (DIST && isDev) ? 'olcesium-debug.js' : 'static/javascript/OpenSeaLab/olcesium.js';

  window.CESIUM_URL = `../${cs}`;
  if (!window.LAZY_CESIUM) {
    document.write(`<scr${'i'}pt type="text/javascript" src="${window.CESIUM_URL}"></scr${'i'}pt>`);
  }
  document.write(`<scr${'i'}pt type="text/javascript" src="../${ol}"></scr${'i'}pt>`);
})();
