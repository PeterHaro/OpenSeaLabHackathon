//OpenLayers 4! Wish me luck!
var map;
var raster = new ol.layer.Tile({
    source: new ol.source.Stamen({
        layer: 'toner'
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

heatmap_layer.getSource().on('addfeature', function(event) {
    var probablyOfMoreThenRegularCatch = event.feature.get("p_high");
    event.feature.set("weigth", probablyOfMoreThenRegularCatch);
});

map = new ol.Map({
    layers: [raster, heatmap_layer],
    target: 'map',
    view: new ol.View({
        center: [0, 0],
        zoom: 2
    })
});

//3D BABY!! WOOP
var ol3d = new olcs.OLCesium({map: map});
const scene = ol3d.getCesiumScene();
const terrainProvider = new Cesium.CesiumTerrainProvider({
  url: '//assets.agi.com/stk-terrain/world',
  requestVertexNormals: true
});
scene.terrainProvider = terrainProvider;
ol3d.setEnabled(true);

