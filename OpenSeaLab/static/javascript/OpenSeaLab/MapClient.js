(function () {
    "use strict";

    var viewer = new Cesium.Viewer('cesiumContainer');


    //TODO: MIGRATE ME INTO ITS OWN FILE:
    function bilinearInterpolateVector(x, y, g00, g10, g01, g11) {
        var rx = (1 - x);
        var ry = (1 - y);
        var a = rx * ry, b = x * ry, c = rx * y, d = x * y;
        var u = g00[0] * a + g10[0] * b + g01[0] * c + g11[0] * d;
        var v = g00[1] * a + g10[1] * b + g01[1] * c + g11[1] * d;
        return [u, v, Math.sqrt(u * u + v * v)];
    }

    /**
     * @returns {Number} returns remainder of floored division, i.e., floor(a / n). Useful for consistent modulo
     *          of negative numbers. See http://en.wikipedia.org/wiki/Modulo_operation.
     */
    function floorMod(a, n) {
        var f = a - n * Math.floor(a / n);
        // HACK: when a is extremely close to an n transition, f can be equal to n. This is bad because f must be
        //       within range [0, n). Check for this corner case. Example: a:=-1e-16, n:=10. What is the proper fix?
        return f === n ? 0 : f;
    }

    /**
     * @returns {Boolean} true if the specified value is not null and not undefined.
     */
    function isValue(x) {
        return x !== null && x !== undefined;
    }

    function netcdfHeader(time, lat, lon, center) {
        return {
            lo1: lon.sequence.start,
            la1: lat.sequence.start,
            dx: lon.sequence.delta,
            dy: -lat.sequence.delta,
            nx: lon.sequence.size,
            ny: lat.sequence.size,
            refTime: time.data[0],
            forecastTime: 0,
            centerName: center
        };
    }

    var sample_wind_data;
    $.getJSON("/cesium/sample_wind", {}).done(function (data) {
        var uData = data[0].data, vData = data[1].data;
        var getData = function (index) {
            return [uData[index], vData[index]];
        };
        var header = data[0].header;
        var startLon = header.lo1, startLat = header.la1; // ORIGIN :: E, N
        var deltaLon = header.dx, deltaLat = header.dy; //Distance between grid points, in deg
        var nx = header.nx, ny = header.ny; //Number of points
        var date = new Date(header.refTime);

        // http://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_table3-4.shtml
        var grid = [], p = 0;
        var points = [];
        var isContinuous = Math.floor(nx, deltaLon) >= 360;
        for (var j = 0; j < ny; j++) {
            var row = [];
            for (var i = 0; i < nx; i++, p++) {
                row[i] = getData(p);
            }
            if (isContinuous) {
                row.push(row[0]);
            }
            grid[j] = row;
        }

        //Inner method for interpolation (color sinews)
        function interpolate(λ, φ) {
            var i = floorMod(λ - startLon, 360) / deltaLon;  // calculate longitude index in wrapped range [0, 360)
            var j = (startLat - φ) / deltaLat;                 // calculate latitude index in direction +90 to -90

            //         1      2           After converting λ and φ to fractional grid indexes i and j, we find the
            //        fi  i   ci          four points "G" that enclose point (i, j). These points are at the four
            //         | =1.4 |           corners specified by the floor and ceiling of i and j. For example, given
            //      ---G--|---G--- fj 8   i = 1.4 and j = 8.3, the four surrounding grid points are (1, 8), (2, 8),
            //    j ___|_ .   |           (1, 9) and (2, 9).
            //  =8.3   |      |
            //      ---G------G--- cj 9   Note that for wrapped grids, the first column is duplicated as the last
            //         |      |           column, so the index ci can be used without taking a modulo.

            var fi = Math.floor(i), ci = fi + 1;
            var fj = Math.floor(j), cj = fj + 1;


            var row;
            if ((row = grid[fj])) {
                var g00 = row[fi];
                var g10 = row[ci];
                if (isValue(g00) && isValue(g10) && (row = grid[cj])) {
                    var g01 = row[fi];
                    var g11 = row[ci];
                    if (isValue(g01) && isValue(g11)) {
                        // All four points found, so interpolate the value.
                        return bilinearInterpolateVector(i - fi, j - fj, g00, g10, g01, g11);
                    }
                }
            }
            console.log("cannot interpolate: " + λ + "," + φ + ": " + fi + " " + ci + " " + fj + " " + cj);
            return null;
        }

   //     console.log(grid);
        var parseDataFunction = function (cb) {
            for (j = 0; j < ny; j++) {
                row = grid[j] || [];
                for (i = 0; i < nx; i++) {
                    cb(floorMod(180 + startLon + i * deltaLon, 360) - 180, startLat - j * deltaLat, row[i]);
                }
            }
        };

        //var retval = [];
        // for (j = 0; j < ny; j++) {
        //   row = grid[j] || [];
        //    for (i = 0; i < nx; i++) {
        //         retval.push((floorMod(180 + startLon + i * deltaLon, 360) - 180, startLat - j * deltaLat, row[i]));
        //      }
        //   }
        //console.log(retval);
        //GET X, Y, DATA
        parseDataFunction(function (x, y, val) {
            if (isValue(val)) {

            }
        });
    });


    //HEATMAP
    var bounds = {
        west: -5.97033,
        east: 52.333,
        south: 17.33333,
        north: 75
    };

    // init heatmap
    var heatMap = CesiumHeatmap.create(
        viewer, // your cesium viewer
        bounds, // bounds for heatmap layer
        {
            // heatmap.js options go here
            // maxOpacity: 0.3
        }
    );

    $.getJSON("/load_prediction_heatmap", {}).done(function (data) {
        var heatmap_data = [];
        data.forEach(function(heatmap_container, index) {
            heatmap_data.push({
                "x" : heatmap_container["lon"],
                "y" : heatmap_container["lat"],
                "value" : ((+heatmap_container["p_high"]))
            })
        });
        heatMap.setWGS84Data(0, 100, heatmap_data);
    });

})();