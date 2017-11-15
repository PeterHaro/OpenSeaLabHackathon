var debug = true;
var proposalsInProgramBarChart = dc.rowChart("#programme-bar-chart");
var actionTypePieChart = dc.pieChart("#action-type-pie-chart");
var involvedPartiesChart = dc.pieChart("#involved-parties--chart");

var programNameCutoffLength = 55;
// LOAD DATA

$.getJSON("/h2020/get_data", {}).done(function (data) {
    data.shift(); //Remove CSV header
    var ndx = crossfilter(data);
    var all = ndx.groupAll();

    //0 = programme
    var involvedPartiesDimension = ndx.dimension(function (d) {
        var retval;

        if(d[7]) {
            retval = d[7].split(new RegExp("[&,]"));
        }
        if(d[8]) {
            if(retval) {
                d[8].split(new RegExp("[,]")).forEach(function(d) {
                    retval.push(d);
                });

            } else {
                retval = d[8].split(new RegExp("[,]"));
            }
        }

        return retval ? retval : ["No parties listed"];
    }, true);
    var programmeNameDimension = ndx.dimension(function (d) {
        return d[0] ? d[0] : "No program listed";
    });
    var actionTypeDimension = ndx.dimension(function (d) {
        if(!d[5]) {
            return ["No type listed"];
        }
        return d[5].split(new RegExp("[,-]"));
    }, true);


    var programmeGroup = programmeNameDimension.group().reduceCount();
    var actionTypeGroup = actionTypeDimension.group();
    var involvedPartiesGroup = involvedPartiesDimension.group();

    proposalsInProgramBarChart
        .width(360)
        .height(360)
        .margins({top: 20, left: 10, right: 10, bottom: 20})
        .group(programmeGroup)
        .dimension(programmeNameDimension)
        // Assign colors to each value in the x scale domain
        .ordinalColors(['#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#dadaeb'])
        .label(function (d) {
            return d.key.length < programNameCutoffLength ? d.key : (d.key.substring(0, programNameCutoffLength) + "...");
        })
        // Title sets the row text
        .title(function (d) {
            return d.key;
        })
        .elasticX(true)
        .xAxis().ticks(4);

    actionTypePieChart.width(300)
        .height(180)
        .radius(80)
        .cx(85)
        .innerRadius(30)
        //.margins({top: 0, right: 50, bottom: 20, left: 40})
        .dimension(actionTypeDimension)
        .group(actionTypeGroup)
        .slicesCap(10)
        .legend(dc.legend().x(176).y(10));

    involvedPartiesChart
        .height(180)
        .radius(80)
        .cx(85)
        .innerRadius(30)
        .slicesCap(10)
        //.margins({top: 0, right: 50, bottom: 20, left: 40})
        .dimension(involvedPartiesDimension)
        .group(involvedPartiesGroup)
        .legend(dc.legend().x(176).y(10));

    //simply call `.renderAll()` to render all charts on the page
    dc.renderAll();
    dc.filterAll();
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
