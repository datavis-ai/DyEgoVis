/*
基于vue.js的d3力导引布局函数.
参数说明:
graph={ // 图数据
  nodes:[{id:x, name:x, value:x}, ...],
  links:[{source:x, target:x, value: weight}, ...]
},
isDirected=true/false, // 图的方向性.
layoutSettings={ // 布局参数配置.
  linkLength: 50, // 边的长度. layoutSettings.linkLength
  chargeStrength: -200, // 力导引力度大小.
  edgeMode: "line", // 边模式:curve-曲线, line-直线.
  labelDisplay: true,
  limitBox: false,
   nodeColor:"#FF8700", // 节点的填充颜色.
   baseSize=10, // 节点的基本大小.
},
svgId // svg的id.
svgWidth,svgHeight // svg的宽和高.
circleClickEvent // 节点点击事件回调函数,用于写节点点击执行的内容.
linkClickEvent // 边点击事件回调函数,用于写点击边执行的内容.
callbackMouseOver(node, mouseState) //鼠标悬浮回调函数.node:鼠标悬浮的节点{id:x, name:x, value:x, r:x},mouseState:鼠标的状态,两种"mouseout" + "mouseover"
layoutEnd // 布局结束之后要执行的函数.
*/
import * as d3 from '../../static/js/d3.v4.min.js'
// let globalSvg = null;
// import $ from '../../static/js/jquery.min.js' // 如果组件里面没有引用则需要取消这行的注释.
function d3GraphLayout(graph=null, isDirected=false, layoutSettings=null, svgId=null, svgWidth=500, svgHeight=500, circleClickEvent=null, linkClickEvent=null, callbackMouseOver=null, layoutEnd=null, svgForExportCallback=null){ 
                      
                      $("#" + svgId + " > *").remove(); // 清除svg中旧的内容.                                         
                      $("#" + svgId).css("width", svgWidth);
                      $("#" + svgId).css("height", svgHeight);
                      // 画布设置
                      let svg = d3.select("#" + svgId);
                      let  linkedByIndex = {};  // 先清空this_.linkedByIndex,避免影响下一次布局鼠标悬浮事件.                      
                      let opacityMouseover = 0.1;
                      let opacityMouseout = 0.3;
                      // fixme: 如果是有向图,则绘制箭头. 
                      if(isDirected){ // 如果是有向图.
                          
                          svg.append("defs").selectAll("marker")
                             .data(["suit", "licensing", "resolved"]) // .data([{id:"end-arrow", opacity:1}, {id:"end-arrow-fade", opacity:0.1}])
                            // .data([{id: "end-arrow", opacity: opacityMouseout}, {id: "end-arrow-fade", opacity: opacityMouseover}]) // 注意:id是箭头元素的id,所以用#end-arrow来表示.
                            // .data(["end-arrow", "end-arrow-fade"])
                            .enter().append("marker")
                              .attr("id", function(d) { return d; })
                              .attr("viewBox", "0 -5 10 10")
                              .attr("refX", 10)
                              .attr("refY", 0)
                              .attr("markerWidth", 9)
                              .attr("markerHeight", 5)
                              .attr("opacity", 0.6)
                              .attr("orient", "auto")
                            .append("path")
                              .attr("d", "M0,-5L10,0L0,5");                          
                           
                      }                
                       
                      getGraphNodeSize(graph, layoutSettings.baseSize); // 获得节点的半径.
                      // 颜色配置
                      let color = d3.scaleOrdinal(d3.schemeCategory20);
                       
                      // 力导引参数配置.
                      let forceLink = d3.forceLink().id(function (d) {
                                            return d.id;
                                        })
                                        .distance(function (d) {                                            
                                            return layoutSettings.linkLength;
                                        });                                          
                                        
                      let simulation = d3.forceSimulation()                          
                          .force("link", forceLink)
                          .force("charge", d3.forceManyBody().strength(layoutSettings.chargeStrength))  // +表示吸引力, -表示排斥力, 当边的长度变大时,应当增大排斥力, -150
                         
                          .force("center", d3.forceCenter(svgWidth / 2, svgHeight / 2)); 
                          
                      let g = svg.append("g")
                                 .attr("class", "everything");               
                        
                        let link=null;
                        if(isDirected){ //如果有向. 
                          if(layoutSettings.edgeMode == "curve"){
                              // 创建边
                              link = g.append("g")
                                      .attr("class", "links")         
                                      // .selectAll("line")
                                      .selectAll("path")
                                      .data(graph.links)
                                      // .enter().append("line")
                                      .enter().append("path")
                                      .attr('marker-end','url(#resolved)');
                                      
                              link.style('fill', 'none')
                                  .style('stroke', 'grey') // stroke-opacity
                                  .style('stroke-opacity', opacityMouseout)
                                  .style("stroke-width", function(d) { return Math.sqrt(d.value); });
                          }
                          if(layoutSettings.edgeMode == "line"){
                              // 创建边
                              link = g.append("g")
                                      .attr("class", "links")         
                                      .selectAll("line")                                      
                                      .data(graph.links)
                                      .enter().append("line")                                      
                                      .attr('marker-end','url(#resolved)')
                                      .attr("stroke", "grey")
                                      .style('stroke-opacity', opacityMouseout)
                                      .attr("stroke-width", function(d) { return Math.sqrt(d.value); });
                               
                          }
                          
                        }
                        else{

                          if(layoutSettings.edgeMode == "curve"){
                             link = g.append("g")
                                      .attr("class", "links")    
                                      .selectAll("path")
                                      .data(graph.links)                                      
                                      .enter().append("path");          
                                       
                             link.style('fill', 'none')
                                .style('stroke', 'grey')
                                .style('stroke-opacity', opacityMouseout)
                                .style("stroke-width", function(d) { return Math.sqrt(d.value); });

                          }
                          if(layoutSettings.edgeMode == "line"){
                             link = g.append("g")
                                    .attr("class", "links")         
                                      .selectAll("line")                                      
                                      .data(graph.links)
                                      .enter().append("line")                                     
                                      .attr("stroke", "grey")
                                      .style('stroke-opacity', opacityMouseout)
                                      .attr("stroke-width", function(d) { return Math.sqrt(d.value); });   

                          }
                          
                        }
                        
                        // 创建节点
                        let node = g.append("g")
                                      .attr("class", "nodes")
                                      .selectAll("g")
                                      .data(graph.nodes)
                                      .enter().append("g")
                                      .attr("class", "node");
                        
                        // 节点形状
                        let circles = node.append("circle")
                                          // .attr("class", "nodecircle")
                                          // .attr("id", function(d){
                                          //      return d.id;  // 以节点id作为circle标签的id.
                                          // })                                          
                                          .attr("class", function(d){
                                               return "nodecircle" + " " + d.id;  // 以节点id作为circle标签的class之一.
                                          })
                                          .attr("r", function(d){
                                              
                                             // return Math.log(multiple*d.value) / Math.log(2) + 5;  
                                              return d.r;                                 
                                            
                                          })
                                          .attr("fill", function(d) {
                                                return layoutSettings.nodeColor; // 节点的颜色.橙色.
                                          })
                                          .call(d3.drag()
                                              .on("start", function (d) {
                                                      if (!d3.event.active) simulation.alphaTarget(0.3).restart();
                                                      d.fx = d.x;
                                                      d.fy = d.y;
                                                })
                                              .on("drag", function (d) {
                                                      d.fx = d3.event.x;
                                                      d.fy = d3.event.y;
                                                  })
                                              .on("end", function (d) {
                                                    if (!d3.event.active) simulation.alphaTarget(0);
                                                    d.fx = null;
                                                    d.fy = null;
                                                }));
                        // let remainingNeighborsCodedCircle = node.append("circle")
                        //                   // .attr("class", "nodecircle")
                        //                   // .attr("id", function(d){
                        //                   //      return d.id;  // 以节点id作为circle标签的id.
                        //                   // })                                          
                        //                   .attr("class", function(d){
                        //                        return "nodecircle-neighbors";  // 以节点id作为circle标签的class之一.
                        //                   })
                        //                   .attr("r", function(d){
                                              
                        //                      // return Math.log(multiple*d.value) / Math.log(2) + 5;  
                        //                       return 1;                                 
                                            
                        //                   })
                        //                   .attr("fill", function(d) {
                        //                         return layoutSettings.remainingNeighborsColor; // 节点的颜色.橙色.
                        //                   });
                                          // .call(d3.drag()
                                          //     .on("start", function (d) {
                                          //             if (!d3.event.active) simulation.alphaTarget(0.3).restart();
                                          //             d.fx = d.x;
                                          //             d.fy = d.y;
                                          //       })
                                          //     .on("drag", function (d) {
                                          //             d.fx = d3.event.x;
                                          //             d.fy = d3.event.y;
                                          //         })
                                          //     .on("end", function (d) {
                                          //           if (!d3.event.active) simulation.alphaTarget(0);
                                          //           d.fx = null;
                                          //           d.fy = null;
                                          //       })); 
                        // 节点标签
                        // let lables = node.append("text")  // 显示节点的标签.
                        //                 .text(function(d) {return d.name;}) // d.name;                             
                        //                 .attr('x', 10)
                        //                 .attr('y', 3);
                        let lables = node.append("text")  // 显示节点的标签.
                                      .text(function(d) {
                                          if(d.name.length > layoutSettings.nodeLabelTextMaxLen){
                                            return d.name.slice(0,layoutSettings.nodeLabelTextMaxLen) + "...";
                                          }
                                          else{
                                            return d.name;
                                          }
                                          
                                      })                          
                                      // .attr('x', 10)
                                      .attr('x', function(d){
                                        return d.r + 4;
                                      })
                                      .attr('y', 3);
                        
                        if(layoutSettings.labelDisplay){ // 显示标签.
                          $("#" + svgId + " .nodes text").css("display", "block"); // 全部显示.
                        }
                        else{
                          $("#" + svgId + " .nodes text").css("display", "none"); // 全部不显示.
                        }
                        // TODO: 添加事件.
                        if(circleClickEvent != null){
                          circles.on("click", circleClickEvent);// circleClickEvent是回调函数,注意,js中函数也可以作为参数.  
                        }                                            
                        //原来是circles,只凸显节点,标签正常显示,改成node后,节点及其标签一起凸显.                       
                        circles.on("mouseover", fade(node, link, opacityMouseover, isDirected, svgId, layoutSettings, linkedByIndex, callbackMouseOver, "mouseover", false)).on("mouseout", fade(node, link, opacityMouseout, isDirected, svgId, layoutSettings, linkedByIndex, callbackMouseOver, "mouseout", false));
                         
                        if(linkClickEvent != null){
                          link.on("click", linkClickEvent);
                        }                        

                        // 开始布局 节点+边
                        simulation
                            .nodes(graph.nodes)
                            .on("tick", function() { // tick是一个监听事件, 只要拖动节点就会触发该事件,更新节点+边的坐标                             
                                if(layoutSettings.edgeMode == "curve"){
                                    link.attr("d", function(d) {                                       
                                       
                                      let sourceX = d.source.x;
                                      let sourceY = d.source.y;
                                      let targetX = d.target.x;
                                      let targetY = d.target.y;

                                      let theta = Math.atan((targetX - sourceX) / (targetY - sourceY));
                                      let phi = Math.atan((targetY - sourceY) / (targetX - sourceX));

                                      let sinTheta = d.source.r * Math.sin(theta);
                                      let cosTheta = d.source.r * Math.cos(theta);
                                      let sinPhi = d.target.r * Math.sin(phi);
                                      let cosPhi = d.target.r * Math.cos(phi);

                                      // Set the position of the link's end point at the source node
                                      // such that it is on the edge closest to the target node
                                      if (d.target.y > d.source.y) {
                                          sourceX = sourceX + sinTheta;
                                          sourceY = sourceY + cosTheta;
                                      }
                                      else {
                                          sourceX = sourceX - sinTheta;
                                          sourceY = sourceY - cosTheta;
                                      }

                                      // Set the position of the link's end point at the target node
                                      // such that it is on the edge closest to the source node
                                      if (d.source.x > d.target.x) {
                                          targetX = targetX + cosPhi;
                                          targetY = targetY + sinPhi;    
                                      }
                                      else {
                                          targetX = targetX - cosPhi;
                                          targetY = targetY - sinPhi;   
                                      }

                                      // Draw an arc between the two calculated points
                                      let dx = targetX - sourceX,
                                          dy = targetY - sourceY,
                                          dr = Math.sqrt(dx * dx + dy * dy);
                                      return "M" + sourceX + "," + sourceY + "A" + dr + "," + dr + " 0 0,1 " + targetX + "," + targetY;
                                    });
                                  }
                                  if(layoutSettings.edgeMode == "line"){                                     

                                      link
                                      .attr("x1", function (d) { return d.source.x; })
                                      .attr("y1", function (d) { return d.source.y; })
                                      .attr("x2", function (d) {
                                          return calculateX(d.target.x, d.target.y, d.source.x, d.source.y, d.target.r);
                                      })
                                      .attr("y2", function (d) {
                                          return calculateY(d.target.x, d.target.y, d.source.x, d.source.y, d.target.r);
                                      });
                                  }
                                  
                                  if(layoutSettings.limitBox){  // 将D3布局图限制在一个盒子里面.\
                                    let radius = 10;
                                    node
                                      .attr("transform", function(d) {
                                        d.x = Math.max(radius, Math.min(width - radius, d.x));
                                        d.y = Math.max(radius, Math.min(height - radius, d.y));
                                        return "translate(" + d.x + "," + d.y + ")";
                                      });
                                  }
                                  else{  // D3布局图不受限制.
                                    node
                                    .attr("transform", function(d) {
                                        return "translate(" + d.x + "," + d.y + ")";
                                    });
                                      
                                  }
                                  
                        })                      
                        .on('end', function(){
                            graph.links.forEach(function(d) { // 如果放在mainviewD3Layout里面则d.source.index没有定义,因为还没有布局好,只有布局好了之后才有d.source.index,所以放在布局后,获得linkedByIndex,这样在鼠标悬浮事件中就可以检测到了.          
                              linkedByIndex[d.source.index + "," + d.target.index] = 1; // {'1,2':1, '2,3':1}                              
                            });                            
                            if(layoutEnd != null){
                               layoutEnd(); //布局结束后要执行的内容.
                            }
                            // svgForExport = svg;                         
                        });

                        simulation.force("link")
                            .links(graph.links); 
                       
                      let zoomHandler = d3.zoom()
                                          .on("zoom", function (){                                   
                                            g.attr("transform", d3.event.transform);                                   
                                        });
                      zoomHandler(svg); // 可以缩放.                       
                      svg.on("dblclick.zoom", null); // fixme:失能双击放大.
                      svgForExportCallback(svg);
                      // globalSvg = svg;
                      // console.log("svgForExport"); console.log(svgForExport);                

           }

function isConnected(a, b, linkedByIndex, isDirected, isConsiderDirecter) { 
  if(isConsiderDirecter){
     if(isDirected) // 只显示有方向性的节点
     {
       return linkedByIndex[a.index + "," + b.index]|| a.index == b.index;  
     }
     else // 显示无方向性的节点
     {
       return linkedByIndex[a.index + "," + b.index] || linkedByIndex[b.index + "," + a.index] || a.index == b.index; 
     }
  }
  else{
    return linkedByIndex[a.index + "," + b.index] || linkedByIndex[b.index + "," + a.index] || a.index == b.index; 
  }
 
    
}
function fade(node, link, opacity, isDirected, svgId, layoutSettings, linkedByIndex, callbackMouseOver, state, isConsiderDirecter) {
     /*
说明:标签是否显示的控制参数由layoutSettings传入,这样的好处是layoutSettings是对象,是地址传入,一旦在外面改变该地址对应的值就能直接反映在函数中,而不需要再次执行函数.
     */
      
      return function(d) {  // d 鼠标悬浮处的节点对象, o 所有节点对象.          
          node.style("stroke-opacity", function(o) { // 节点高亮.
              
              let isCon = isConnected(d, o, linkedByIndex, isDirected, isConsiderDirecter); // false
              // let thisOpacity = isCon ? 1 : opacity;  //opacity越小越透明, d + o如果有连接关系
              let thisOpacity = null;
              if(state == "mouseover"){
                thisOpacity = isCon ? 1 : 0.1;
                this.setAttribute('fill-opacity', thisOpacity); // 邻居不透明,其余节点透明.
              }
              else{
                thisOpacity = isCon ? 1 : 1;
                this.setAttribute('fill-opacity', thisOpacity); // 邻居不透明,其余节点透明.
              }
                         
              // 显示标签.
              if(layoutSettings.labelDisplay){ // 显示标签.
                $("#" + svgId + " .nodes text").css("display", "block"); // 全部显示.
              }
              else{ // 不显示标签.
                
                 if(isCon){ // 连接点显示标签.
                      // console.log("stroke-opacity this");console.log(this.children().last());
                      if(state == "mouseover"){ // mouse离开.
                        $(this).children().last().css("display", "block"); // 原来的.
                        // $(this).children().css("display", "block"); // 修改后
                      }
                      else{
                        $(this).children().last().css("display", "none");
                        // console.log("$(this).children()");console.log($(this).children());
                      }
                      
                  }
                  else{ // 其他点不显示.
                    $(this).children().last().css("display", "none");
                  }
              }
              
              return thisOpacity;
          });

          link.style("stroke-opacity", function(o) { // 边高亮. o 所有边{source:{}, target:{}}
           
            if(isConsiderDirecter){
                if(isDirected)  // 只显示有方向性的边
                {
                  if(state === "mouseover"){
                     return o.source === d ? 1 : opacity; // 出度边不透明显示.
                  }
                  if(state === "mouseout"){
                    return o.source === d ? opacity : opacity; // 出度边不透明显示.
                  }                  
                }
                else  // 显示无方向性的边.
                {
                  if(state === "mouseover"){
                     return o.source === d || o.target === d ? 1 : opacity; // 邻居边不透明显示.
                  }
                  if(state === "mouseout"){
                     return o.source === d || o.target === d ? opacity : opacity; // 邻居边不透明显示.
                  }
                }
            }
            else{
                  if(state === "mouseover"){
                     return o.source === d || o.target === d ? 1 : opacity; // 邻居边不透明显示.
                  }
                  if(state === "mouseout"){
                     return o.source === d || o.target === d ? opacity : opacity; // 邻居边不透明显示.
                  }
            }
            
          });
          if(isDirected){
            // if(state === "mouseover"){
            //    link.attr('marker-end', o => (o.source === d  ? 'url(#resolved)' : 0.1));
            // }
            // if(state === "mouseout"){
            //    link.attr('marker-end', o => (o.source === d  ? 'url(#resolved)' : 'url(#resolved)')); // opacity === 1, 保证鼠标移开后,能正常恢复箭头.如果没有这一项则箭头消失.
            // }
            link.attr('marker-end', o => (state === "mouseout" || o.source === d || o.target === d  ? 'url(#resolved)' : 1));
            
          }
          if(callbackMouseOver != null){
            let mouseState = "";
            // if(opacity == 1){ //opacity==1时,正常显示,鼠标离开.
            //   mouseState = "mouseout";
            // }
            // else{
            //   mouseState = "mouseover";
            // }
            if(state == "mouseout"){ //opacity==1时,正常显示,鼠标离开.
              mouseState = "mouseout";
            }
            if(state == "mouseover"){
              mouseState = "mouseover";
            }
            callbackMouseOver(d, mouseState);
          }                    
          
      };
}

function calculateX(tx, ty, sx, sy, radius){
    if(tx == sx) return tx;                 //if the target x == source x, no need to change the target x.
    var xLength = Math.abs(tx - sx);    //calculate the difference of x
    var yLength = Math.abs(ty - sy);    //calculate the difference of y
    //calculate the ratio using the trigonometric function
    var ratio = radius / Math.sqrt(xLength * xLength + yLength * yLength);
    if(tx > sx)  return tx - xLength * ratio;    //if target x > source x return target x - radius
    if(tx < sx) return  tx + xLength * ratio;    //if target x < source x return target x + radius
}

function calculateY(tx, ty, sx, sy, radius){
    if(ty == sy) return ty;                 //if the target y == source y, no need to change the target y.
    var xLength = Math.abs(tx - sx);    //calculate the difference of x
    var yLength = Math.abs(ty - sy);    //calculate the difference of y
    //calculate the ratio using the trigonometric function
    var ratio = radius / Math.sqrt(xLength * xLength + yLength * yLength);
    if(ty > sy) return ty - yLength * ratio;   //if target y > source y return target x - radius
    if(ty < sy) return ty + yLength * ratio;   //if target y > source y return target x - radius
}
function getGraphNodeSize(graph, baseSize){  // 用于决定节点大小的倍数.
      let nodes = graph.nodes;
      let tempList = [];
      let multiple = 0;
      nodes.forEach(function(i){           
        tempList.push(i.value);
      });
       
      // let maxValue = Math.max.apply(null,tempList);
      let minValue = Math.min.apply(null,tempList);
      // console.log("maxValue");console.log(maxValue);
      // console.log("minValue");console.log(minValue);
      if(minValue < 0.0000001){
        multiple = baseSize / 0.000001;
      }
      else{
        multiple = baseSize / minValue;
      }              
      // console.log("multiple");console.log(multiple);
      // 添加节点的半径.
      nodes.forEach(function(i){  // i={id:x, name:x, value:x}           
        if(i.value < 0.0000001){
          i.r = Math.log(baseSize) / Math.log(2) + 5;
        }
        else{
          i.r = Math.log(multiple*i.value) / Math.log(2) + 5;
        }                                 
      });
             
}

export {
  d3GraphLayout  
}