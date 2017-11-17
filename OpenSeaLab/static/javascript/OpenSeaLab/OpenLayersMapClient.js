//OpenLayers 4! Wish me luck!
var map;
var raster = new ol.layer.Tile({
    source: new ol.source.Stamen({
        layer: 'toner'
    })
});

var openSeaMapLayer = new ol.layer.Tile({
    source: new ol.source.OSM({
        layer: "openseamap"
    })
});

var heatmap_layer = new ol.layer.Heatmap({
    source: new ol.source.Vector({
        url: '/load_prediction_geojson_heatmap',
        format: new ol.format.GeoJSON()
    }),
    blur: 15,
    radius: 2
});

heatmap_layer.getSource().on('addfeature', function (event) {
    var probablyOfMoreThenRegularCatch = event.feature.get("p_high");
    event.feature.set("weigth", probablyOfMoreThenRegularCatch);
});


//LAYER SWITCHER
window.app = {};
var app = window.app;
app.LayerSwitcherControl = function (opt_options) {
    var options = opt_options || {};
    var button = document.createElement("a");
    button.innerHTML = "<a href=\"#\" data-activates=\"slide-out\" class=\"ol-control button-collapse\"><i class=\"material-icons\">layers</i></a>"
    //button.innerHTML = "N";
    var this_ = this;
    var handle_layerswitcher = function () {
        //OPEN/CLOSE LAYERSWITCHER
    };
    //button.addEventListener('click', handle_layerswitcher, false);
    //button.addEventListener('touchstart', handle_layerswitcher, false);
    var element = document.createElement('div');
    element.className = 'rotate-north ol-unselectable ol-control';
    element.appendChild(button);
    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });
};
ol.inherits(app.LayerSwitcherControl, ol.control.Control);

map = new ol.Map({
    controls: ol.control.defaults({
        attributionOptions: /** @type {olx.control.AttributionOptions} */ ({
            collapsible: false
        })
    }).extend([
        new app.LayerSwitcherControl()
    ]),
    layers: [openSeaMapLayer, heatmap_layer],
    target: 'map',
    view: new ol.View({
        center: [0, 0],
        zoom: 2
    })
});

//Ice consentration map TODO: FIXME: Figure out why the tiled one doesnt work, then port to tiled
/*var ice_chart_consentration_map = new ol.layer.Tile({
    visible: false,
    name: "ice_chart",
    source: new ol.source.TileWMS({
        url: 'https://geo.barentswatch.no/geoserver/bw/wms',
        params: {
            "FORMAT": "image/png",
            "VERSION": "1.1.1",
            "TILED": true,
            STYLES: "",
            "LAYERS": "bw:icechart_latest",
            tilesOrigin: -180 + "," + 40,
        },
        serverType: "geoserver"
    })
});

map.addLayer(ice_chart_consentration_map); */
var untiled = new ol.layer.Image({
    source: new ol.source.ImageWMS({
        ratio: 1,
        url: 'https://geo.barentswatch.no/geoserver/bw/wms',
        params: {
            'FORMAT': "image/png",
            'VERSION': '1.1.1',
            STYLES: '',
            LAYERS: 'bw:icechart_latest',
        }
    })
});
map.addLayer(untiled);
map.updateSize();


/*
//COOL SHIT BRUH!
var windy;
var canvas = document.getElementById('windyMap');

function refreshWindy() {
    if (!windy) {
        return;
    }
    windy.stop();
    var mapSize = map.getSize();
    var extent = map.getView().calculateExtent(mapSize);
    extent = ol.proj.transformExtent(extent, 'EPSG:3857', 'EPSG:4326');

    canvas.width = mapSize[0];
    canvas.height = mapSize[1];

    windy.start(
        [[0, 0], [canvas.width, canvas.height]],
        canvas.width,
        canvas.height,
        [[extent[0], extent[1]], [extent[2], extent[3]]]
    );
}

fetch('/static/data/gfs.json').then(function(response) {
  return response.json();
}).then(function(json) {
  windy = new Windy({canvas: canvas, data: json });
  refreshWindy();
});

map.on('moveend', refreshWindy);
*/
