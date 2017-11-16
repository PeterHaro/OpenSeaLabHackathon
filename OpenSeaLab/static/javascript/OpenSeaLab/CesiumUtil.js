function CesiumUtility() {
    var defaultKMLEyeOffset = new Cesium.Cartesian3(0.0, 5000.0, 0.0);
    var defaultScaleByDistance = new Cesium.NearFarScalar(1, 0.5, 1, 0.3);
    var defaultTranslucency = new Cesium.NearFarScalar(1.5e2, 1, 3.0e6, 0);
}

CesiumUtility.prototype.LoadWms = function(layerId, geoDataSrc, geoLayers, noFeatures) {
    var src;
    if (noFeatures) {
        src = viewer.imageryLayers.addImageryProvider(new Cesium.WebMapServiceImageryProvider({
            url: geoDataSrc,
            layers: geoLayers,
            sourceUri: geoDataSrc,
            enablePickFeatures: false,
            tilingScheme: new Cesium.WebMercatorTilingScheme(),
            parameters: {
                transparent: true,
                format: 'image/png' //TODO: Fetch from config
            }
        }));
    } else {
        src = viewer.imageryLayers.addImageryProvider(new Cesium.WebMapServiceImageryProvider({
            url: geoDataSrc,
            layers: geoLayers,
            sourceUri: geoDataSrc,
            tilingScheme: new Cesium.WebMercatorTilingScheme(),
            parameters: {
                transparent: true,
                format: 'image/png' //TODO: Fetch from config
            }
        }));
    }
    activeLayers[layerId] = src;
    loadSliders(src, layerId);
};


//https://idpgis.ncep.noaa.gov/arcgis/services/NWS_Observations/radar_base_reflectivity/MapServer/WMSServer?request=GetCapabilities&service=WMS