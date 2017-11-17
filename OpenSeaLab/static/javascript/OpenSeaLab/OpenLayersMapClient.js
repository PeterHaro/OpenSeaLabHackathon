//OpenLayers 4! Wish me luck!
var map;
//POPUPS
var container = document.getElementById('popup');
var content = document.getElementById('popup-content');
var closer = document.getElementById('popup-closer');

//__END_POPUPS
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
    name: "predicted_fish",
    source: new ol.source.Vector({
        url: '/load_prediction_geojson_heatmap',
        format: new ol.format.GeoJSON()
    }),
    blur: 15,
    radius: 2
});
heatmap_layer.set("name", "predicted_fish");

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

//SET VISIBILITY
var setLayerVisibility = function (name) {
    map.getLayers().forEach(function (layer) {
        if (layer.get("name") === name) {
            layer.setVisible(!layer.getVisible());
        }
    });
};


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

var closed_zones_wms = new ol.source.TileWMS({
    url: 'https://geo.barentswatch.no/geoserver/bw/wms',
    params: {
        'FORMAT': "image/png",
        'VERSION': '1.1.1',
        tiled: true,
        STYLES: '',
        LAYERS: 'bw:jmelding_view',
        tilesOrigin: -1 + "," + -1
    }
});

var closed_zones = new ol.layer.Tile({
    visible: true,
    source: closed_zones_wms
});

untiled.set("name", "ice_chart");
closed_zones.set("name", "closed messages");
map.addLayer(untiled);
map.addLayer(closed_zones);
map.updateSize();

//Add layers to layerswitcher
map.getLayers().forEach(function (layer) {
    console.log(layer.get("name"));
    var layerswitching_menu = document.getElementById("slide-out");
    if (layer.get("name") !== undefined) {
        var li = document.createElement("li");
        li.innerHTML = "<input type='checkbox' onclick =setLayerVisibility('" + layer.get("name") + "') id='" + layer.get("name") + "'checked='checked'/>" + "<label for='" + layer.get("name") + "'>" + layer.get("name") + "</label>";
        ;
        layerswitching_menu.appendChild(li);
    }
});

var displayFeatureInfo = function (pixel) {
    var features = [];
    map.forEachFeatureAtPixel(pixel, function (feature, layer) {
        features.push(feature);
        console.log(layer);
    });
    if (features.length > 0) {
        console.log(features);
    }
};

//ANCHOR FOR POPUPS TO GET A FIX POSS IN MAp
var overlay = new ol.Overlay(/** @type {olx.OverlayOptions} */ ({
    element: container,
    autoPan: true,
    autoPanAnimation: {
        duration: 250
    }
}));

map.addOverlay(overlay);
closer.onclick = function () {
    overlay.setPosition(undefined);
    closer.blur();
    return false;
};

//Feature selection! Wish me luck!
map.on('singleclick', function (evt) {
    var coordinate = evt.coordinate;
    var view = map.getView();
    var viewResolution = view.getResolution();
    var url = closed_zones_wms.getGetFeatureInfoUrl(
        evt.coordinate, viewResolution, view.getProjection(),
        {'INFO_FORMAT': 'application/json', 'FEATURE_COUNT': 50});
    if (url) {
        console.log(url);
        var parser = new ol.format.GeoJSON();
        $.ajax({
            url: url,
            dataType: 'json',
            jsonpCallback: 'parseResponse'
        }).then(function (response) {
            var result = parser.readFeatures(response);
            console.log(result);
            content.innerHTML = "<h4>Closed area</h4>"+  "<p>Name: " + result[0].P.name + "</p><p> Closed for: " + result[0].P.type_name + "</p>" + "<p>" + result[0].P.description + "</p>";
            overlay.setPosition(coordinate);
        });
    }
});

/*
    <li>
        <input type="checkbox" id="test5"/>
        <label for="test5">Red</label>
    </li>
 */

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
