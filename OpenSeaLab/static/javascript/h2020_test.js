var debug = true;
var proposalsInProgramBarChart = dc.rowChart("#programme-bar-chart");
var actionTypePieChart = dc.pieChart("#action-type-pie-chart");

// LOAD DATA

$.getJSON("/h2020/get_data", {}).done(function (data) {
    data.shift(); //Remove CSV header
    var ndx = crossfilter(data);
    var all = ndx.groupAll();

    //0 = programme
    var programmeNameDimension = ndx.dimension(function (d) {
        return d[0];
    });
    var actionTypeDimension = ndx.dimension(function (d) {
        if(!d[5]) {
            return "";
        }
        return d[5].split("-");
    });

    var programmeGroup = programmeNameDimension.group().reduceCount();
    var actionTypeGroup = actionTypeDimension.group().reduceCount();
    proposalsInProgramBarChart
        .width(360)
        .height(360)
        .margins({top: 20, left: 10, right: 10, bottom: 20})
        .group(programmeGroup)
        .dimension(programmeNameDimension)
        // Assign colors to each value in the x scale domain
        .ordinalColors(['#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#dadaeb'])
        .label(function (d) {
            return d.key;
        })
        // Title sets the row text
        .title(function (d) {
            return d.value;
        })
        .elasticX(true)
        .xAxis().ticks(4);

    actionTypePieChart.width(180)
        .height(180)
        .radius(80)
        .innerRadius(30)
        //.margins({top: 0, right: 50, bottom: 20, left: 40})
        .dimension(actionTypeDimension)
        .group(actionTypeGroup);


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
