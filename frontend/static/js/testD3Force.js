import * as d3 from '../../static/js/d3.v4.min.js'
function maotyForce(graph, selectorPath, width, height, radius=15) {
    //create somewhere to put the force directed graph
    var svg = d3.select(selectorPath);
//        width = +svg.attr("width"),
//        height = +svg.attr("height");
//    var radius = 15;

    //set up the simulation
    var simulation = d3.forceSimulation()
                        //add nodes
                        .nodes(graph.nodes);


    var link_force =  d3.forceLink(graph.links)
                            .id(function(d) { return d.name; });

    var charge_force = d3.forceManyBody()
        .strength(-100);

    var center_force = d3.forceCenter(width / 2, height / 2);

    simulation
        .force("charge_force", charge_force)
        .force("center_force", center_force)
        .force("links",link_force);


    //add tick instructions:
    simulation.on("tick", tickActions );

    //draw lines for the links
    var link = svg.append("g")
          .attr("class", "links")
        .selectAll("line")
        .data(graph.links)
        .enter().append("line")
          .attr("stroke-width", 2)
          .style("stroke", linkColour);

    //draw circles for the nodes
    var node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(graph.nodes)
            .enter()
            .append("circle")
            .attr("r", radius)
            .attr("fill", circleColour);

    var drag_handler = d3.drag()
        .on("start", drag_start)
        .on("drag", drag_drag)
        .on("end", drag_end);

    drag_handler(node)



    /** Functions **/

    //Function to choose what color circle we have
    //Let's return blue for males and red for females
    function circleColour(d){
        if(d.sex =="M"){
            return "blue";
        } else {
            return "pink";
        }
    }

    //Function to choose the line colour and thickness
    //If the link type is "A" return green
    //If the link type is "E" return red
    function linkColour(d){
        if(d.type == "A"){
            return "green";
        } else {
            return "red";
        }
    }



    //drag handler
    //d is the node
    function drag_start(d) {
     if (!d3.event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function drag_drag(d) {
      d.fx = d3.event.x;
      d.fy = d3.event.y;
    }


    function drag_end(d) {
      if (!d3.event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }


    function tickActions() {
        //constrains the nodes to be within a box
          node
            .attr("cx", function(d) { return d.x = Math.max(radius, Math.min(width - radius, d.x)); })
            .attr("cy", function(d) { return d.y = Math.max(radius, Math.min(height - radius, d.y)); });

        link
            .attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });
    }

}


export {
  maotyForce  
}