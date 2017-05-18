(function() {
    var uStates = {};

    function toolTip(d, data) {
        var n = d.properties["STATE_NAME"]
        var value = data[(d.properties["STATE_NAME"])]
        return "<h4>" + n + "</h4>" + value;
    }

    uStates.draw = function(id) {
        data = {
            "New South Wales": 1.1,
            "Victoria": 1.5,
            "Queensland": 0.7,
            "South Australia": 0.8,
            "Western Australia": 0.9,
            "Tasmania": 0.3,
            "Northern Territory": 0.2,
            "Australian Capital Territory": 0.4,
        };

        function mouseOver(d) {
            d3.select("#tooltip").transition().duration(200).style("opacity", .9);
            d3.select("#tooltip").html(toolTip(d, data)).style("left", (d3.event.pageX) + "px").style("top", (d3.event.pageY - 28) + "px");
        }

        function mouseOut() {
            d3.select("#tooltip").transition().duration(500).style("opacity", 0);
        }

        var w = 960,
            h = 500;
        var z = d3.scaleOrdinal(d3.schemeCategory10);
        var fill = d3.scaleLog()
            .domain(d3.extent(d3.values(data)))
            .range(["lightsteelblue", "steelblue"]);
        var projection = d3.geoMercator()
            .center([125, -24])
            .translate([250, 180])
            .scale(700);
        var path = d3.geoPath()
            .projection(projection);
        var svg = d3.select(id).append("svg")
            .attr("width", w)
            .attr("height", h);
        var states = svg.append("g")
        d3.json("./data/aus-states.geojson", function(collection) {
            states.selectAll("path")
                .data(collection.features)
                .enter().append("path")
                .attr("class", "state")
                .attr("fill", function(d) {
                    return fill(data[(d.properties["STATE_NAME"])]);
                })
                .attr("d", path)
                .on("mouseover", mouseOver).on("mouseout", mouseOut);
        });
    }
    this.uStates = uStates;

    var barChart = {}

    barChart.draw = function(id, data) {
        console.log(data);
        var margin = {
                top: 20,
                right: 20,
                bottom: 70,
                left: 40
            },
            width = 450 - margin.left - margin.right,
            height = 300 - margin.top - margin.bottom;


        // set the ranges
        // var x = d3.scale.ordinal();
        var x = d3.scaleBand().rangeRound([0, width]);

        var y = d3.scaleLinear().range([height, 0]);

        // define the axis
        var xAxis = d3.axisBottom(x);

        var yAxis = d3.axisLeft(y)
            .ticks(10);

        // add the SVG element
        var svg = d3.select(id).append("svg")
            .attr("class", "chart")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform",
                "translate(" + margin.left + "," + margin.top + ")");


        // scale the range of the data
        x.domain(data.map(function(d) {
            return Object.keys(d)[0];
        }));


        y.domain([0, d3.max(data, function(d) {
            return Object.values(d)[0];
        })]);


        // add axis
        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis)
            .selectAll("text")
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", "-.55em")
            .attr("transform", "rotate(-45)");

        svg.append("text")
            .attr("transform", "translate(" + (width/2) + " ," + (height + margin.top + 30) + ")")
            .attr("dy", ".71em")
            .style("text-anchor", "middle")
            .text("University");

        svg.append("g")
            .attr("class", "y axis")
            .call(yAxis)
            .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 5)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text("Frequency");

            // text label for the y axis
        svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 0 - margin.left)
            .attr("x",0 - (height / 2))
            .attr("dy", ".71em")
            .style("text-anchor", "middle")
            .text("Percentage of tweets");


        // Add bar chart
        svg.selectAll("bar")
            .data(data)
            .enter().append("rect")
            .attr("class", "bar")
            .attr("x", function(d) {
                return x(Object.keys(d)[0]);
            })
            .attr("width", x.bandwidth()-5)
            .attr("y", function(d) {
                return y(Object.values(d)[0]);
            })
            .attr("height", function(d) {
                return height - y(Object.values(d)[0]);
            });


    }
    this.barChart = barChart;

})();
