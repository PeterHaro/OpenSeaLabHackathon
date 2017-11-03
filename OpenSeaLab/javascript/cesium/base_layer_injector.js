function CesiumBaseLayerInjection() {
    this._imageryViewModels = [];
    this._terrainProviders = [];
}

CesiumBaseLayerInjection.prototype.init = function () {
    this.generateDefaultImegaryViewModels();
    this.generateDefaultTerrainProviders();
};

CesiumBaseLayerInjection.prototype.generateDefaultImegaryViewModels = function () {
    this.AddImageryViewModel(this.getDarkMatterImageryViewModel());
    this.AddImageryViewModel(this.getMidnightImageryViewModel());
    this.AddImageryViewModel(this.getERSIOceanImageryViewModel());
    this.AddImageryViewModel(this.getCVBlueImageryViewModel());
    this.AddImageryViewModel(this.getStatmanWatercolorImageryViewModel());
};

CesiumBaseLayerInjection.prototype.generateDefaultTerrainProviders = function () {
    this.AddTerrainProvider(this.getWGS84TerrainModel());
    this.AddTerrainProvider(this.getSTKMeshesTerrainModel());
};


// _UTILITY_IMAGERY_AND_TERRAIN__
CesiumBaseLayerInjection.prototype.getDarkMatterImageryViewModel = function () {
    return new Cesium.ProviderViewModel({
        name: 'Dark Matter',
        iconUrl: 'assets/images/cesium/dark-matter.jpg',
        tooltip: 'Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.',
        creationFunction: function () {
            return new Cesium.UrlTemplateImageryProvider({
                url: 'http://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
                credit: 'Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
            });
        }
    });
};

CesiumBaseLayerInjection.prototype.getCVBlueImageryViewModel = function () {
    return new Cesium.ProviderViewModel({
        name: 'CV Blue',
        iconUrl: 'assets/images/cesium/cv-blue.jpg',
        tooltip: 'CartoDB World Flat Blue. Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.',
        creationFunction: function () {
            return new Cesium.UrlTemplateImageryProvider({
                url: 'https://cartocdn_{s}.global.ssl.fastly.net/base-flatblue/{z}/{x}/{y}.png',
                credit: 'Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
            });
        }
    });
};

CesiumBaseLayerInjection.prototype.getMidnightImageryViewModel = function () {
    return new Cesium.ProviderViewModel({
        name: 'Midnight',
        iconUrl: 'assets/images/cesium/midnight-commander.jpg',
        tooltip: 'CartoDB World Midnight Commander. Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.',
        creationFunction: function () {
            return new Cesium.UrlTemplateImageryProvider({
                url: 'https://cartocdn_{s}.global.ssl.fastly.net/base-midnight/{z}/{x}/{y}.png',
                credit: 'Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
            });
        }
    });
};

CesiumBaseLayerInjection.prototype.getERSIOceanImageryViewModel = function () {
    return new Cesium.ProviderViewModel({
        name: 'ESRI Ocean',
        iconUrl: 'assets/images/cesium/esri-ocean.jpg',
        tooltip: 'Includes bathymetry, marine water body names, undersea feature names, and derived depth values in meters.',
        creationFunction: function () {
            return new Cesium.ArcGisMapServerImageryProvider({
                url: 'http://services.arcgisonline.com/arcgis/rest/services/Ocean_Basemap/MapServer'
            });
        }
    });
};

CesiumBaseLayerInjection.prototype.getStatmanWatercolorImageryViewModel = function () {
    return new Cesium.ProviderViewModel({
        name: 'Watercolor',
        iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/stamenWatercolor.png'),
        tooltip: 'Reminiscent of hand drawn maps maps.stamen.com',
        creationFunction: function () {
            return new Cesium.UrlTemplateImageryProvider({
                url: 'http://tile.stamen.com/watercolor/{z}/{x}/{y}.jpg',
                credit: 'Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under CC BY SA.'
            });
        }
    });
};

CesiumBaseLayerInjection.prototype.getWGS84TerrainModel = function () {
    return new Cesium.ProviderViewModel({
        name: 'WGS84 Ellipsoid',
        iconUrl: Cesium.buildModuleUrl('Widgets/Images/TerrainProviders/Ellipsoid.png'),
        tooltip: 'WGS84 standard ellipsoid, also known as EPSG:4326',
        creationFunction: function () {
            return new Cesium.EllipsoidTerrainProvider();
        }
    });
};

CesiumBaseLayerInjection.prototype.getSTKMeshesTerrainModel = function () {
    return new Cesium.ProviderViewModel({
        name: 'STK World Terrain meshes',
        iconUrl: Cesium.buildModuleUrl('Widgets/Images/TerrainProviders/STK.png'),
        tooltip: 'High-resolution, mesh-based terrain for the entire globe. Free for use on the Internet. Closed-network options are available.\nhttp://www.agi.com',
        creationFunction: function () {
            return new Cesium.CesiumTerrainProvider({
                url: '//assets.agi.com/stk-terrain/world',
                requestWaterMask: true,
                requestVertexNormals: true
            });
        }
    });
};


// _END_UTILITY_IMAGERY_AND_TERRAIN__

// _GETTERS_AND_SETTERS__

CesiumBaseLayerInjection.prototype.getImageryViewModels = function () {
    return this._imageryViewModels;
};

CesiumBaseLayerInjection.prototype.getTerrainProviders = function () {
    return this._terrainProviders;
};

CesiumBaseLayerInjection.prototype.SetImageryViewModels = function (models) {
    this._imageryViewModels = models
};

CesiumBaseLayerInjection.prototype.SetTerrainProviders = function (providers) {
    this._terrainProviders = providers;
};

CesiumBaseLayerInjection.prototype.AddImageryViewModel = function (model) {
    this._imageryViewModels.push(model);
};

CesiumBaseLayerInjection.prototype.AddTerrainProvider = function (provider) {
    this._terrainProviders.push(provider);
};

// _END_GETTERS_AND_SETTERS__
