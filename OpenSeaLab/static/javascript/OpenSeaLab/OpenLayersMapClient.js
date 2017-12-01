//OpenLayers 4! Wish me luck!
var map;
//POPUPS
var container = document.getElementById('popup');
var content = document.getElementById('popup-content');
var closer = document.getElementById('popup-closer');
var dateContainer = document.getElementById('date-input-container-context');
var dateCloser = document.getElementById('popup-closer-context');
//var content = document.getElementById('popup-content');
var currentDate = "20130301";

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

var catchFeatureStyle =  function(feature, resolution) {
    var quantity = feature.P.total_quantity;

    return new ol.style.Style({
        image: new ol.style.Circle({
            radius: 7,
            stroke: new ol.style.Stroke({
                color: '#000000',
                width: 1
            }),
            fill: new ol.style.Fill({
                color: quantity < 2000 ? "#00ff00" : quantity < 4000 ? "#ffff00" : quantity < 6000 ? "#ffbf00" : quantity < 8000 ? "#ff8000" : "#ff0000"
            })
        })
    });
}



var highlightStyle = new ol.style.Style({
    stroke: new ol.style.Stroke({
        color: '#f00',
        width: 1
    }),
        fill: new ol.style.Fill({
        color: 'rgba(255,0,0,0.1)'
    })
});

var catchLayer = new ol.layer.Vector({
    name: "catch_data",
    source: new ol.source.Vector({
      url: '/load_catch_data?date=20131101',
      format: new ol.format.GeoJSON()
    })
    ,style: catchFeatureStyle
});
// catchLayer.setStyle(catchFeatureStyle);

var heatmapSource = new ol.source.Vector({
        url: '/load_prediction_geojson_heatmap?date=20131101',
        format: new ol.format.GeoJSON()
    });

var heatmap_layer = new ol.layer.Heatmap({
    name: "predicted_fish_high",
    source: heatmapSource,
    blur: 15,
    radius: 2,
    weight: function(feature){
        return feature.get("p_high")
    }
});

heatmap_layer.getSource().on('addfeature', function (event) {
    var probablyOfMoreThenRegularCatch = event.feature.get("p_high");
    event.feature.set("weigth", probablyOfMoreThenRegularCatch);
});
// heatmap_layer.setVisible(false);

var prediction_low_heatmap_layer = new ol.layer.Heatmap({
    name: "predicted_fish_low",
    source: heatmapSource,
    blur: 15,
    radius: 2,
    weight: function(feature){
        return feature.get("p_low")
    }
});
prediction_low_heatmap_layer.setVisible(false);

prediction_low_heatmap_layer.getSource().on('addfeature', function (event) {
    var probablyOfLessThanRegularCatch = event.feature.get("p_low");
    event.feature.set("weigth", probablyOfLessThanRegularCatch);
});

var prediction_mid_heatmap_layer = new ol.layer.Heatmap({
    name: "predicted_fish_mid",
    source: heatmapSource,
    blur: 15,
    radius: 2,
    weight: function(feature){
        return feature.get("p_mid")
    }
});
prediction_mid_heatmap_layer.setVisible(false);

prediction_mid_heatmap_layer.getSource().on('addfeature', function (event) {
    var probablyOfRegularCatch = event.feature.get("p_mid");
    event.feature.set("weigth", probablyOfRegularCatch);
});

var sinmod_temperature_layer = new ol.layer.Heatmap({
    name: "sinmod_temp",
    source: new ol.source.Vector({
        //url: '/load_sinmod_geojson_temp',
        format: new ol.format.GeoJSON()
    }),
    blur: 15,
    radius: 2
});

sinmod_temperature_layer.getSource().on('addfeature', function (event) {
    var sinmodTemperature = event.feature.get("Temperature");
    event.feature.set("weigth", sinmodTemperature);
});
sinmod_temperature_layer.setVisible(false);

var emodnet_temperature_layer = new ol.layer.Heatmap({
    name: "emodnet_temp",
    source: new ol.source.Vector({
        url: '/load_sinmod_geojson_temp',
        format: new ol.format.GeoJSON()
    }),
    blur: 15,
    radius: 2
});

emodnet_temperature_layer.getSource().on('addfeature', function (event) {
    var temperature = event.feature.get("temp");
    event.feature.set("weigth", temperature);
});
emodnet_temperature_layer.setVisible(false);


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
    layers: [openSeaMapLayer, heatmap_layer, prediction_mid_heatmap_layer, prediction_low_heatmap_layer, sinmod_temperature_layer, emodnet_temperature_layer],
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
closed_zones.set("name", "closed_messages");
map.addLayer(untiled);
map.addLayer(closed_zones);
map.addLayer(catchLayer);
map.updateSize();

//Add layers to layerswitcher
map.getLayers().forEach(function (layer) {
    console.log(layer.get("name"));
    var layerswitching_menu = document.getElementById("slide-out");
    if (layer.get("name") !== undefined) {
        var li = document.createElement("li");
        if(layer.get("name") == 'sinmod_temp' || layer.get("name") == 'emodnet_temp'  || layer.get("name") == 'predicted_fish_low' || layer.get("name") == 'predicted_fish_mid') {
                    li.innerHTML = "<input type='checkbox' onclick =setLayerVisibility('" + layer.get("name") + "') id='" + layer.get("name") + "'/>" + "<label for='" + layer.get("name") + "'>" + layer.get("name") + "</label>";
        } else {
                    li.innerHTML = "<input type='checkbox' onclick =setLayerVisibility('" + layer.get("name") + "') id='" + layer.get("name") + "'checked='checked'/>" + "<label for='" + layer.get("name") + "'>" + layer.get("name") + "</label>";

        }
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
//    autoPan: true,
//    autoPanAnimation: {
//        duration: 250
//    }
}));

var dateOverlay = new ol.Overlay(/** @type {olx.OverlayOptions} */ ({
    element: dateContainer,
//    autoPan: true,
//    autoPanAnimation: {
//        duration: 250
//    }
}));

map.addOverlay(overlay);
map.addOverlay(dateOverlay);

closer.onclick = function () {
    overlay.setPosition(undefined);
    closer.blur();
    return false;
};

dateCloser.onclick = function () {
    dateOverlay.setPosition(undefined);
    dateOverlay.blur();
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

// the style function for the feature overlay returns
// a text style for point features and the highlight
// style for other features (polygons in this case)
function styleFunction(feature, resolution) {
    var style;
    var geom = feature.getGeometry();
    if (geom.getType() == 'Point') {
      var text = feature.get('text');
      baseTextStyle.text = text;
      // this is inefficient as it could create new style objects for the
      // same text.
      // A good exercise to see if you understand would be to add caching
      // of this text style
      var isoCode = feature.get('isoCode').toLowerCase();
      style = new ol.style.Style({
        text: new ol.style.Text(baseTextStyle),
        image: new ol.style.Icon({
          src: '../assets/img/flags/'+isoCode+'.png'
        }),
        zIndex: 2
      });
    } else {
      style = highlightStyle;
    }

    return [style];
}

var featureOverlay = new ol.layer.Vector({
        source: new ol.source.Vector(),
        map: map,
        style: function(feature) {
          return highlightStyle;
        }
      });

  var highlight;
  var displayFeatureInfo = function(pixel) {

    var feature = map.forEachFeatureAtPixel(pixel, function(feature) {
      return feature;
    });

    var info = document.getElementById('info');
    if (feature) {

        speciesDistributionString = "";

        if(feature.P["species_and_catch"] != null) {
            feature.P.species_and_catch.forEach(function(entry) {
                speciesDistributionString += "<p>" + entry[0] + ": " + entry[1] + "kg</p>";
            });
        } else {
            return;
        }

        info.innerHTML = "<p>Total fangst: " + feature.P.total_quantity + " kg</p>" +
            "<p>Fartøy: " + (feature.P.vesselName == "Nordørn" ? "Tråler 22" : (feature.P.vesselName == "Nordstar" ? "Tråler 23" : feature.P.vesselName)) + "</p>" +
            "Fiskeslag: " + speciesDistributionString;

        var geometry = feature.getGeometry();
        var coord = geometry.getCoordinates();
        overlay.setPosition(coord);

        var content = document.getElementById('popup-content');
        content.innerHTML = info.innerHTML;
    } else {
      info.innerHTML = '&nbsp;';
    }

    if (feature !== highlight) {
      if (highlight) {
        featureOverlay.getSource().removeFeature(highlight);
      }
      if (feature) {
        featureOverlay.getSource().addFeature(feature);
      }
      highlight = feature;
    }

  };

  map.on('pointermove', function(evt) {
    if (evt.dragging) {
      return;
    }
    var pixel = map.getEventPixel(evt.originalEvent);
    displayFeatureInfo(pixel);
  });

  map.on('click', function(evt) {
    displayFeatureInfo(evt.pixel);
  });

var contextmenu = new ContextMenu({
  width: 180,
  items: [
      {
        text: 'Ny dato',
        callback: setDateFieldPosition
      }
  ]
});
map.addControl(contextmenu);

function setDateFieldPosition() {
    dateOverlay.setPosition(map.getView().getCenter());
}

function getDateData(date) {

    var submittedDate = document.getElementById("date-input-field-context").value;

    dateOverlay.setPosition(undefined);
    dateCloser.blur();

    var catchLayer = map.getLayers().a[8];

    if(date != null) {
        submittedDate = date;
    }

    if(submittedDate == currentDate) {
        return;
    }

    var catchSource = new ol.source.Vector({
      url: '/load_catch_data?date=' + submittedDate,
      format: new ol.format.GeoJSON()
    });

    catchLayer.setSource(catchSource);

    var predictionSource = new ol.source.Vector({
      url: '/load_prediction_geojson_heatmap?date=' + submittedDate,
      format: new ol.format.GeoJSON()
    });
    heatmap_layer.setSource(predictionSource);
    prediction_low_heatmap_layer.setSource(predictionSource);
    prediction_mid_heatmap_layer.setSource(predictionSource);
    // catchLayer.changed();
}

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
