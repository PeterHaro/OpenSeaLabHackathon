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

        console.log(grid);
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
        north: 79.84
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

// random example data
    var data = [{"x": 147.1383442264, "y": -41.4360048372, "value": 76}, {
        "x": 147.1384363011,
        "y": -41.4360298848,
        "value": 63
    }, {"x": 147.138368102, "y": -41.4358360603, "value": 1}, {
        "x": 147.1385627739,
        "y": -41.4358799123,
        "value": 21
    }, {"x": 147.1385138501, "y": -41.4359327669, "value": 28}, {
        "x": 147.1385031219,
        "y": -41.4359730105,
        "value": 41
    }, {"x": 147.1384127393, "y": -41.435928255, "value": 75}, {
        "x": 147.1384551136,
        "y": -41.4359450132,
        "value": 3
    }, {"x": 147.1384927196, "y": -41.4359158649, "value": 45}, {
        "x": 147.1384938639,
        "y": -41.4358498311,
        "value": 45
    }, {"x": 147.1385183299, "y": -41.4360213794, "value": 93}, {
        "x": 147.1384007925,
        "y": -41.4359860133,
        "value": 46
    }, {"x": 147.1383604844, "y": -41.4358298672, "value": 54}, {
        "x": 147.13851025,
        "y": -41.4359098303,
        "value": 39
    }, {"x": 147.1383874733, "y": -41.4358511035, "value": 34}, {
        "x": 147.1384981796,
        "y": -41.4359355403,
        "value": 81
    }, {"x": 147.1384504107, "y": -41.4360332348, "value": 39}, {
        "x": 147.1385582664,
        "y": -41.4359788335,
        "value": 20
    }, {"x": 147.1383967364, "y": -41.4360581999, "value": 35}, {
        "x": 147.1383839615,
        "y": -41.436016316,
        "value": 47
    }, {"x": 147.1384082712, "y": -41.4358423338, "value": 36}, {
        "x": 147.1385092651,
        "y": -41.4358577623,
        "value": 69
    }, {"x": 147.138360356, "y": -41.436046789, "value": 90}, {
        "x": 147.138471893,
        "y": -41.4359184292,
        "value": 88
    }, {"x": 147.1385605689, "y": -41.4360271359, "value": 81}, {
        "x": 147.1383585714,
        "y": -41.4359362476,
        "value": 32
    }, {"x": 147.1384939114, "y": -41.4358844253, "value": 67}, {
        "x": 147.138466724,
        "y": -41.436019121,
        "value": 17
    }, {"x": 147.1385504355, "y": -41.4360614056, "value": 49}, {
        "x": 147.1383883832,
        "y": -41.4358733544,
        "value": 82
    }, {"x": 147.1385670669, "y": -41.4359650236, "value": 25}, {
        "x": 147.1383416534,
        "y": -41.4359310876,
        "value": 82
    }, {"x": 147.138525285, "y": -41.4359394661, "value": 66}, {
        "x": 147.1385487719,
        "y": -41.4360137656,
        "value": 73
    }, {"x": 147.1385496029, "y": -41.4359187277, "value": 73}, {
        "x": 147.1383989222,
        "y": -41.4358556562,
        "value": 61
    }, {"x": 147.1385499424, "y": -41.4359149305, "value": 67}, {
        "x": 147.138404523,
        "y": -41.4359563326,
        "value": 90
    }, {"x": 147.1383883675, "y": -41.4359794855, "value": 78}, {
        "x": 147.1383967187,
        "y": -41.435891185,
        "value": 15
    }, {"x": 147.1384610005, "y": -41.4359044797, "value": 15}, {
        "x": 147.1384688489,
        "y": -41.4360396127,
        "value": 91
    }, {"x": 147.1384431875, "y": -41.4360684409, "value": 8}, {
        "x": 147.1385411067,
        "y": -41.4360645847,
        "value": 42
    }, {"x": 147.1385237178, "y": -41.4358843181, "value": 31}, {
        "x": 147.1384406464,
        "y": -41.4360003831,
        "value": 51
    }, {"x": 147.1384679169, "y": -41.4359950456, "value": 96}, {
        "x": 147.1384194314,
        "y": -41.4358419739,
        "value": 22
    }, {"x": 147.1385049792, "y": -41.4359574813, "value": 44}, {
        "x": 147.1384097378,
        "y": -41.4358598672,
        "value": 82
    }, {"x": 147.1384993219, "y": -41.4360352975, "value": 84}, {
        "x": 147.1383640499,
        "y": -41.4359839518,
        "value": 81
    }];
    var valueMin = 0;
    var valueMax = 100;

// add data to heatmap
    heatMap.setWGS84Data(valueMin, valueMax, data);

})();