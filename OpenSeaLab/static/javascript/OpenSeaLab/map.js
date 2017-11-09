//ENTRY POINT FOR THE CESIUM APPLICATION
(function () {
    "use strict";
    var yearPerSec = 86400 * 365;
    var gregorianDate = new Cesium.GregorianDate();
    var cartesian3Scratch = new Cesium.Cartesian3();

    var OpenSeaLabCesiumClient = function () {
        // private declarations
        this._name = "Health and Wealth";
        this._entityCollection = new Cesium.EntityCollection();
        this._clock = new Cesium.DataSourceClock();
        this._clock.startTime = Cesium.JulianDate.fromIso8601("1800-01-02");
        this._clock.stopTime = Cesium.JulianDate.fromIso8601("2009-01-02");
        this._clock.currentTime = Cesium.JulianDate.fromIso8601("1800-01-02");
        this._clock.clockRange = Cesium.ClockRange.LOOP_STOP;
        this._clock.clockStep = Cesium.ClockStep.SYSTEM_CLOCK_MULTIPLIER;
        this._clock.multiplier = yearPerSec * 5;
        this._changed = new Cesium.Event();
        this._error = new Cesium.Event();
        this._isLoading = false;
        this._loading = new Cesium.Event();
        this._year = 1800;
        this._wealthScale = d3.scale.log().domain([300, 1e5]).range([0, 10000000.0]);
        this._healthScale = d3.scale.linear().domain([10, 85]).range([0, 10000000.0]);
        this._populationScale = d3.scale.sqrt().domain([0, 5e8]).range([5.0, 30.0]);
        this._colorScale = d3.scale.category20c();
        this._selectedEntity = undefined;
    };

    Object.defineProperties(OpenSeaLabCesiumClient.prototype, {
        name: {
            get: function () {
                return this._name;
            }
        },
        clock: {
            get: function () {
                return this._clock;
            }
        },
        entities: {
            get: function () {
                return this._entityCollection;
            }
        },
        selectedEntity: {
            get: function () {
                return this._selectedEntity;
            },
            set: function (e) {
                if (Cesium.defined(this._selectedEntity)) {
                    var entity = this._selectedEntity;
                    entity.polyline.material.color = new Cesium.ConstantProperty(Cesium.Color.fromCssColorString(this._colorScale(entity.region)));
                }
                if (Cesium.defined(e)) {
                    e.polyline.material.color = new Cesium.ConstantProperty(Cesium.Color.fromCssColorString('#00ff00'));
                }
                this._selectedEntity = e;
            }
        },
        /**
         * Gets a value indicating if the data source is currently loading data.
         * @memberof OpenSeaLabCesiumClient.prototype
         * @type {Boolean}
         */
        isLoading: {
            get: function () {
                return this._isLoading;
            }
        },
        /**
         * Gets an event that will be raised when the underlying data changes.
         * @memberof OpenSeaLabCesiumClient.prototype
         * @type {Event}
         */
        changedEvent: {
            get: function () {
                return this._changed;
            }
        },
        /**
         * Gets an event that will be raised if an error is encountered during
         * processing.
         * @memberof OpenSeaLabCesiumClient.prototype
         * @type {Event}
         */
        errorEvent: {
            get: function () {
                return this._error;
            }
        },
        /**
         * Gets an event that will be raised when the data source either starts or
         * stops loading.
         * @memberof OpenSeaLabCesiumClient.prototype
         * @type {Event}
         */
        loadingEvent: {
            get: function () {
                return this._loading;
            }
        }
    });

    OpenSeaLabCesiumClient.prototype.loadUrl = function (url) {
        if (!Cesium.defined(url)) {
            throw new Cesium.DeveloperError("url must be defined.");
        }

        var that = this;
        return Cesium.when(Cesium.loadJson(url), function (json) {
            return that.load(json);
        }).otherwise(function (error) {
            this._setLoading(false);
            that._error.raiseEvent(that, error);
            return Cesium.when.reject(error);
        });
    };

    OpenSeaLabCesiumClient.prototype.load = function (data) {
        if (!Cesium.defined(data)) {
            throw new Cesium.DeveloperError("data must be defined.");
        }
        var ellipsoid = viewer.scene.globe.ellipsoid;

        this._setLoading(true);
        var entities = this._entityCollection;
        //It's a good idea to suspend events when making changes to a
        //large amount of entities.  This will cause events to be batched up
        //into the minimal amount of function calls and all take place at the
        //end of processing (when resumeEvents is called).
        entities.suspendEvents();
        entities.removeAll();

        //Once all data is processed, call resumeEvents and raise the changed event.
        entities.resumeEvents();
        this._changed.raiseEvent(this);
        this._setLoading(false);
    };

    OpenSeaLabCesiumClient.prototype._setLoading = function (isLoading) {
        if (this._isLoading !== isLoading) {
            this._isLoading = isLoading;
            this._loading.raiseEvent(this, isLoading);
        }
    };

    OpenSeaLabCesiumClient.prototype._setInfoDialog = function (time) {
        if (Cesium.defined(this._selectedEntity)) {

        }
    };

    OpenSeaLabCesiumClient.prototype.update = function (time) {
        Cesium.JulianDate.toGregorianDate(time, gregorianDate);
        var currentYear = gregorianDate.year + gregorianDate.month / 12;
        if (currentYear !== this._year && typeof window.displayYear !== 'undefined') {
            window.displayYear(currentYear);
            this._year = currentYear;

            this._setInfoDialog(time);
        }

        return true;
    };

    $("#radio").buttonset();
    $("#radio").css("font-size", "12px");
    $("#radio").css("font-size", "12px");
    $("body").css("background-color", "black");

    $("input[name='healthwealth']").change(function (d) {
        var entities = healthAndWealth.entities.entities;
        healthAndWealth.entities.suspendEvents();
        for (var i = 0; i < entities.length; i++) {
            var entity = entities[i];
            if (d.target.id === 'health') {
                entity.polyline.positions = new Cesium.PositionPropertyArray([new Cesium.ConstantPositionProperty(entity.surfacePosition), entity.health]);
            } else {
                entity.polyline.positions = new Cesium.PositionPropertyArray([new Cesium.ConstantPositionProperty(entity.surfacePosition), entity.wealth]);
            }
        }
        healthAndWealth.entities.resumeEvents();
    });

    var viewer = new Cesium.Viewer('cesiumContainer',
        {
            fullscreenElement: document.body,
            infoBox: false
        });



    viewer.animation.viewModel.dateFormatter = function (date, viewModel) {
        Cesium.JulianDate.toGregorianDate(date, gregorianDate);
        return 'Year: ' + gregorianDate.year;
    };
    viewer.animation.viewModel.timeFormatter = function (date, viewModel) {
        return '';
    };
    viewer.scene.skyBox.show = false;
    viewer.scene.sun.show = false;
    viewer.scene.moon.show = false;

    viewer.scene.morphToColumbusView(5.0)

    var healthAndWealth = new OpenSeaLabCesiumClient();
    healthAndWealth.loadUrl('nations_geo.json');
    viewer.dataSources.add(healthAndWealth);

    // If the mouse is over the billboard, change its scale and color
    var highlightBarHandler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    highlightBarHandler.setInputAction(
        function (movement) {
            var pickedObject = viewer.scene.pick(movement.endPosition);
            if (Cesium.defined(pickedObject) && Cesium.defined(pickedObject.id)) {
                if (Cesium.defined(pickedObject.id.nationData)) {
                    sharedObject.dispatch.nationMouseover(pickedObject.id.nationData, pickedObject);
                    healthAndWealth.selectedEntity = pickedObject.id;
                }
            }
        },
        Cesium.ScreenSpaceEventType.MOUSE_MOVE
    );

    var flyToHandler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    flyToHandler.setInputAction(
        function (movement) {
            var pickedObject = viewer.scene.pick(movement.position);

            if (Cesium.defined(pickedObject) && Cesium.defined(pickedObject.id)) {
                sharedObject.flyTo(pickedObject.id.nationData);
            }
        },
        Cesium.ScreenSpaceEventType.LEFT_CLICK
    );

    // Response to a nation's mouseover event
    sharedObject.dispatch.on("nationMouseover.cesium", function (nationObject) {

        $("#info table").remove();
        $("#info").append("<table> \
        <tr><td>Life Expectancy:</td><td>" + parseFloat(nationObject.lifeExpectancy).toFixed(1) + "</td></tr>\
        <tr><td>Income:</td><td>" + parseFloat(nationObject.income).toFixed(1) + "</td></tr>\
        <tr><td>Population:</td><td>" + parseFloat(nationObject.population).toFixed(1) + "</td></tr>\
        </table>\
        ");
        $("#info table").css("font-size", "10px");
        $("#info").dialog({
            title: nationObject.name,
            width: 200,
            height: 150,
            modal: false,
            position: {my: "right center", at: "right center", of: "canvas"},
            show: "slow"
        });
    });


    // define functionality for flying to a nation
    // this callback is triggered when a nation is clicked
    sharedObject.flyTo = function (nationData) {
        var ellipsoid = viewer.scene.globe.ellipsoid;

        var destination = Cesium.Cartographic.fromDegrees(nationData.lon, nationData.lat - 5.0, 10000000.0);
        var destCartesian = ellipsoid.cartographicToCartesian(destination);
        destination = ellipsoid.cartesianToCartographic(destCartesian);

        // only fly there if it is not the camera's current position
        if (!ellipsoid
                .cartographicToCartesian(destination)
                .equalsEpsilon(viewer.scene.camera.positionWC, Cesium.Math.EPSILON6)) {

            viewer.scene.camera.flyTo({
                destination: destCartesian
            });
        }
    };

})();