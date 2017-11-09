var catalogue = function () {
    "use strict";

    var WIND_DATA_DIRECTORY = "../data/";

    /**
     * Returns a date for the chronologically next or previous GFS data layer. How far forward or backward in time
     * to jump is determined by the step. Steps of ±1 move in 3-hour jumps, and steps of ±10 move in 24-hour jumps.
     */
    function gfsStep(date, step) {
        var offset = (step > 1 ? 8 : step < -1 ? -8 : step) * 3, adjusted = new Date(date);
        adjusted.setHours(adjusted.getHours() + offset);
        return adjusted;
    }

    function gfsDate(attr) {
        if (attr.date === "current") {
            // Construct the date from the current time, rounding down to the nearest three-hour block.
            var now = new Date(Date.now()), hour = Math.floor(now.getUTCHours() / 3);
            return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), hour));
        }
        var parts = attr.date.split("/");
        return new Date(Date.UTC(+parts[0], parts[1] - 1, +parts[2], +attr.hour.substr(0, 2)));
    }

}();