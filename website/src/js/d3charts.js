(function() {
  var uStates = {};

  function toolTip(d, data){
  	var n = d.properties["STATE_NAME"]
  	var value = data[(d.properties["STATE_NAME"])]
    return "<h4>"+n+"</h4>" + value;
  }

  uStates.draw = function(id) {
      data = {"New South Wales":8,
        "Victoria":6,
        "Queensland":3,
        "South Australia":7,
        "Western Australia":4,
        "Tasmania": 6,
        "Northern Territory": 7,
        "Australian Capital Territory":5,
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
      		.translate([250,180])
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
})();
