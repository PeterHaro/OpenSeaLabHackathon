var debug = true;
var proposalsInProgramBarChart = dc.rowChart("#programme-bar-chart");

// LOAD DATA

$.getJSON("/get_data", {}).done(function (data) {
    $.each(data.items, function (i, item) {

    });
    var ndx = crossfilter(data);
    var all = ndx.groupAll();

    var programmeNameDimension = ndx.dimension(function (d) {
        return d.Programme;
    });
    var programmeGroup = programmeNameDimension.group();

    proposalsInProgramBarChart/* dc.rowChart('#day-of-week-chart', 'chartGroup') */
        .width(180)
        .height(180)
        .margins({top: 20, left: 10, right: 10, bottom: 20})
        .group(programmeGroup)
        .dimension(programmeNameDimension)
        // Assign colors to each value in the x scale domain
        .ordinalColors(['#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#dadaeb'])
        .label(function (d) {
            return d.key.split('.')[1];
        })
        // Title sets the row text
        .title(function (d) {
            return d.value;
        })
        .elasticX(true)
        .xAxis().ticks(4);


    //simply call `.renderAll()` to render all charts on the page
    dc.renderAll();
    /*
    // Or you can render charts belonging to a specific chart group
    dc.renderAll('group');
    // Once rendered you can call `.redrawAll()` to update charts incrementally when the data
    // changes, without re-rendering everything
    dc.redrawAll();
    // Or you can choose to redraw only those charts associated with a specific chart group
    dc.redrawAll('group');
    */
});