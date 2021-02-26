<template>
  <div id="egonets-time-step">           
    <div id="egonets-time-step-box">      
      <svg id="svg-egonets-time-step" :width="svgWidth" :height="$store.getters.gettimeStepOverviewH + 15">
        <rect id="all-overviews-bg" :width="$store.getters.gettimeStepEgonetW * timestepNum" :height="$store.getters.gettimeStepOverviewH + 15" x="0" y="0" style="fill:white;opacity:1"></rect>
        <g id="track-lines-g" :transform="'translate(' + margin.left + ',' + margin.top + ')'"></g>
        <g id="all-overviews-g" :transform="'translate(' + margin.left + ',' + margin.top + ')'"></g>
      </svg>
    </div>
    <div id="overview-egonetsnp-info"></div> 
  </div>  
</template>

<script>
  import * as d3 from '../../static/js/d3.v4.min.js'
  import {vueFlaskRouterConfig} from '../flaskRouter'
  import bus from '../eventbus.js' // 事件总线.  
  import axios from 'axios'
  import {mapGetters} from "vuex"
  import {jBox} from "../../static/js/jBox.js"
  import {d3GraphLayout} from "../../static/js/forceDyEgonet.js"
  import $ from 'jquery'
  import {d3Lasso} from "../../static/js/lasso.js"
  import * as $$ from "../../static/js/jquery.min.js"
  import "../../static/js/jquery.contextMenu.js"
  import "../../static/js/jquery.ui.position.js" 
    
  export default {
    data() {
      return {
          margin: {left: 10, top: 10, right: 10, bottom: 10}, 
          MARGIN: 5,
          // clickedEgoList: [],          
          lasso: null,
          // egoSelectedLassoList: [] 
          isDragLasso: false,
          jBoxInstance: {
            egosnpDetail: null
          },
          curViewEgo: null,
          curTimeStep: null                 
      }
    },
    computed: {      
      // ...mapGetters([
      //    // "getselectedEgoList",
      //    "gettimeStepList",
      //    "gettimeStepSlice"
      //   ])
    },
    props:[
     "svgWidth",
     // "svgHeight",
     "timestepNum"
    ],
    watch: {
      // timestepNum: function(curVal, oldVal){
      //   let this_ = this;
      //   // this_.addOverviewTimeStep(curVal);
      //   // this_.curTimeSteps = curVal;
      // }
    },
    methods: {      
      getStatDiagramForDetail(dbname, selector, egoInfoObj, barWidth, barHeight, svgHeight, curTimeStep){
          /*
          egoInfoObj = {
            info: {'total_p_num': 1, 
            'ego': '2128276236', 
            'features': {f1: [x,x,x,...], f2: [], ...}, // 原始特征而非统计特征. 
            'name': 'Ping Guo', 
            'p_num_year': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
            'r_interests': 'Parallel coordinates;Data visualization', 
            'org': 'IEEE'},
            ftList: [f1, f2, ..., f6]
          }
          "#overview-dyegonet-info"
           [avg_alter_num, avg_density, avg_tie, avg_alterE_num, avg_alter2_num, avg_alter_alters, total_p_num]
           ['Degree', 'Density', 'Avg_weight', 'num_edges_alters', 'num_2_alters', 'avg_alters_alters'];
        */
        let this_ = this;
        d3.selectAll(selector + " > *").remove();
        let egoInfo = d3.select(selector).append("div").attr("class", "ego-info-div");
        let ftDiv = d3.select(selector).append("div").attr("class", "ft-p-div");      
        let customizeName = ['degree', 'num_edges_alters', 'density', 'avg_weight', 'num_2_alters', 'avg_alters_alters'];
        let curTimeStepIdx = this_.$store.getters.gettimeStepList.indexOf(curTimeStep)
        let barMargin = 2;
        let sliceStartIdx = 0; // 时间区间的起始位置.
        let sliceEndIdx = this_.$store.getters.gettimeStepList.length - 1;
        if(this_.$store.getters.gettimeStepSlice.length > 0){
          sliceStartIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);
          sliceEndIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[1]);
        }
        curTimeStepIdx = curTimeStepIdx - sliceStartIdx;
        // 绘制每个特征 -> 值序列统计图.
        for(let idx=0; idx < egoInfoObj.ftList.length; idx++){
          let ftName = egoInfoObj.ftList[idx];
          // 接下来取出对应的信息, 构建DOM.
          let ftValList = egoInfoObj.info.features[ftName]; // 取出该特征序列值.          
          let newftValList = ftValList.slice(sliceStartIdx, sliceEndIdx + 1); // [x, x, x, ...]
          let maxVal = Math.max(...newftValList);
          // let minVal = Math.min(...newftValList);
          let detaH = 0;
          if(maxVal > 0){
            detaH = barHeight / maxVal;
          }
          let divBox = ftDiv.append("div").attr("class", "ft-div");
          divBox.append("div").attr("class", "dt-ft-tag tooltip").text("TF" + (idx + 1).toString() + ":").append('span').attr("class", "tooltiptext").text(function(){
            return customizeName[idx];
          });
          let svg = divBox.append("svg")
                .attr("class", "static-dt-svg")
                .attr("width", newftValList.length * (barWidth + barMargin) + 4)
                .attr("height", svgHeight);
          for(let i=0; i < newftValList.length; i++){
            svg.append("rect")
             .attr("class", "ftbar")
             .attr("x", i * (barWidth + barMargin))
             .attr("y", svgHeight - detaH * newftValList[i])
             .attr("width", barWidth)
             .attr("height", detaH * newftValList[i])
             .attr("fill", function(){
               if(curTimeStepIdx == i){
                return "#d94801";
               }else{
                return "#253494";
               }
             })
             .append("title")
             .attr("class", "bart")
             .text(function(){
                let timestep = this_.$store.getters.gettimeStepList[sliceStartIdx + i];              
                return "T: " + timestep + ", Val: " + newftValList[i].toFixed(2);
             });
          }
        }
        egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
          return "Timestep: " + curTimeStep;
        });
        egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
          return "Its ego: " + egoInfoObj.info.name;
        });
        if(dbname == "enron"){
          egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
            return "Ego's position: " + egoInfoObj.info.position;
          }); 
        }      
        if(dbname == "tvcg"){
          // total_p_num
          // p_num_year
          // r_interests
          // org        
          egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
            return "Affiliation: " + egoInfoObj.info.org.split(";")[0];
          });
          egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
            let splitArr = egoInfoObj.info.r_interests.split(";"); // [x, x, ...]
            let newStr = "";
            let sLen = splitArr.length;
            if(sLen > 3){
              sLen = 3;
            }
            for(let i = 0; i < sLen; i++){
              if(i < sLen - 1) newStr += splitArr[i] + ", ";
              else newStr += splitArr[i];
            }
            return "Research Interests: " + newStr;
          });
          egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
            return "Total_Pub_Num: " + egoInfoObj.info.total_p_num;
          });                   
          let ftValList = egoInfoObj.info.p_num_year;
          let newftValList = ftValList.slice(sliceStartIdx, sliceEndIdx + 1); // [x, x, x, ...]
          let maxVal = Math.max(...newftValList);          
          let detaH = 0;
          if(maxVal > 0){
            detaH = barHeight / maxVal;
          }
          let divBox = ftDiv.append("div").attr("class", "ft-div");
          divBox.append("div").attr("class", "dt-ft-tag tooltip").attr("style", "font-size:12px").text("NA1:").append('span').attr("class", "tooltiptext").text(function(){
            return "pub_num_per_year";
          });
          let svg = divBox.append("svg")
                .attr("class", "static-dt-svg")
                .attr("width", newftValList.length * (barWidth + barMargin) + 4)
                .attr("height", svgHeight);
          for(let i=0; i < newftValList.length; i++){
            svg.append("rect")
             .attr("class", "ftbar-snp")
             .attr("fill", function(){
               if(curTimeStepIdx == i){
                return "#d94801";
               }else{
                return "#253494";
               }               
             })
             .attr("x", i * (barWidth + barMargin))
             .attr("y", svgHeight - detaH * newftValList[i])
             .attr("width", barWidth)
             .attr("height", detaH * newftValList[i])
             .append("title")
             .attr("class", "bart")
             .text(function(){
                let timestep = this_.$store.getters.gettimeStepList[sliceStartIdx + i];              
                return "T: " + timestep + ", Val: " + newftValList[i].toFixed(2);
             });
          }
        }
      },
      getDyEgonetSnpInfo(egoId, curTimeStep){
        let this_ = this;
        let dbname = this_.$store.getters.getselectedDataset;
        let selector = "#overview-egonetsnp-info"; 
        let barWidth = 4;
        let barHeight = 12;
        let svgHeight = 13;
        // let curTimeStep = "";
        let param = {dbname: dbname, egoId: egoId};
          axios.post(vueFlaskRouterConfig.dyegonetDetail, {
            param: JSON.stringify(param)
        })
        .then((res) => {
            let egoInfoObj = res.data;
            // console.log("getDyEgonetInfo egoInfoObj");console.log(egoInfoObj);
            this_.getStatDiagramForDetail(dbname, selector, egoInfoObj, barWidth, barHeight, svgHeight, curTimeStep);
          })
        .catch((error) => {            
          console.error(error);
        });
      },
      contextMenuForSnp(){
        let this_ = this;
        $.contextMenu({ 
          // fixme: contextMenu插件是一个事件类型的,也就是说,mounted阶段并没有'each-dyegonet-bg'这个元素,需要点击ego后才能渲染出来,但是由于这是一个事件,则直接在mounted里面注册,一旦出现这样的元素则会直接绑定到上面,在这些元素上右键点击触发对应事件.
          selector: '#egonets-time-step .overview-points .point', // 绑定的元素,当在该元素右键时,就会弹出右键选择项目. 验证去掉背景矩形.
          // selector: '.each-dyegonet', // 绑定的元素,当在该元素右键时,就会弹出右键选择项目.
          className: "egonetsnpOVContextMenu",
          callback: function(key, options) {
             let egoId = options.$trigger[0].childNodes[0].attributes[2].nodeValue; // 该dyegonet的ego的ID. 
             let curTimeStep = options.$trigger[0].attributes[1].nodeValue;             
             if(key == "delete"){  // 如果点击的是"delete"选项.
               this_.jBoxInstance.egosnpDetail.open();               
               this_.getDyEgonetSnpInfo(egoId, curTimeStep);
               let pointSt = null;
               if(this_.curViewEgo){
                 pointSt = "#egonets-time-step .overview-points .point[name='" + curTimeStep + "'] circle[name='" + this_.curViewEgo + "']";
                 d3.select(pointSt).attr("stroke", "#d1d1d1").attr("stroke-width", 1);
               }
               pointSt = "#egonets-time-step .overview-points .point[name='" + curTimeStep + "'] circle[name='" + egoId + "']";
               d3.select(pointSt).attr("stroke", "black").attr("stroke-width", 2); // 高亮点.
               this_.curViewEgo = egoId;
               this_.curTimeStep = curTimeStep;
             }
             if(key == "copy"){
              let newEgoId = "txviewg-" + egoId; // "dyegovis-1234", "dyegovis-mao.mty"
              let addnewEgoId = newEgoId.replace(/\./g, "-");
              d3.select("#svg-egonets-time-step .overview-points text." + addnewEgoId + "[name='" + curTimeStep + "']").attr("display", "block");
             }
             if(key == "edit"){
              let newEgoId = "txviewg-" + egoId; // "dyegovis-1234", "dyegovis-mao.mty"
              let addnewEgoId = newEgoId.replace(/\./g, "-");
              d3.select("#svg-egonets-time-step .overview-points text." + addnewEgoId + "[name='" + curTimeStep + "']").attr("display", "none");
             }         
          },
          items: {
              "delete": {name: "View Details"},              
              "copy": {name: "Display Ego Name"},
              "edit": {name: "Hide Ego Name"},
              "quit": {name: "Quit"}
          },
          zIndex: 1200
        });
      },
      getTimestepNum(){
      let this_ = this;
      let timestepNum_ = 0;
      if(this_.$store.getters.gettimeStepSlice.length > 0){
        let startIndex = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);
        let endIndex = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[1]);
        timestepNum_ = endIndex - startIndex + 1;
      }
      else{
        timestepNum_ = this_.$store.getters.gettimeStepList.length;
      }
      return timestepNum_;
     },     
     addOverviewTimeStep(selectedTimestepNum){
        let this_ = this;        
        d3.selectAll("#svg-egonets-time-step #all-overviews-g > *").remove(); // 之前使用select, 应该使用selectAll.
        let overviewg = d3.select("#svg-egonets-time-step #all-overviews-g");
        let startIndex = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);
        for(let i=0; i<selectedTimestepNum; i++){ // 根据时间步数,添加对应的格子,用于绘制egonet.            
            let timestepX = this_.$store.getters.gettimeStepEgonetW * i;
            let eachTimestepG = overviewg.append("g")
                                         .attr("class", "overview-at-timestep" + " overview-" + i)
                                         // .attr("id", "egonet-" + i)
                                         .attr("name", this_.$store.getters.gettimeStepList[startIndex + i]) // name="2001"
                                         .attr("transform", "translate(" +  timestepX + ",0)"); 
            eachTimestepG.append("rect") // 添加snapshot的背景,用于确定绘制图的大小,以及边框样式设计.
                          .attr("class", "overview-bg")
                          .attr("width", this_.$store.getters.gettimeStepEgonetW)
                          .attr("height", this_.$store.getters.gettimeStepOverviewH)
                          .attr("x", 0)
                          .attr("y", 0)
                          .style("fill", "none")
                          .style("stroke", "#aaa") // 背景颜色#aaa
                          .style("opacity", 0.5);            
          }
      },
      drawOverviewTimestep(overviewTimeSteps){
        /*
        overviewTimeSteps={2001: [{ego: "hunter.shively", egoattrs: {…}, fvec: Array(6), point: Array(2)}, ...], ...}
        */
        let this_ = this;        
        if(this_.$store.getters.gettimeStepSlice.length == 0){ //整个时间轴.         
          this_.$store.commit("changedateStringArray", this_.$store.getters.gettimeStepList); // [2001-01, ..., 2002-01], 即切片时间.
        }
        else{ // 时间区间
          let startTime = this_.$store.getters.gettimeStepSlice[0];
          let endTime = this_.$store.getters.gettimeStepSlice[1];
          let startTimeIndex = this_.$store.getters.gettimeStepList.indexOf(startTime);
          let endTimeIndex = this_.$store.getters.gettimeStepList.indexOf(endTime);
          let dateStringArray = this_.$store.getters.gettimeStepList.slice(startTimeIndex, endTimeIndex + 1);
          this_.$store.commit("changedateStringArray", dateStringArray);
        }                 
        for(let i = 0; i < this_.$store.getters.getdateStringArray.length; i++){
          let date = this_.$store.getters.getdateStringArray[i];
          let egoPointList = overviewTimeSteps[date];
          let selectorP = "#svg-egonets-time-step #all-overviews-g .overview-at-timestep[name='" + date + "']";          
          this_.egoNetOverview(selectorP, egoPointList, date, this_.$store.getters.getdateStringArray);
        }
        this_.eventInit(); 
      },
      eventInit(){
        let this_ = this;  
        let svg = d3.select("#svg-egonets-time-step");        
        d3.selectAll("#svg-egonets-time-step .lasso").remove();
        // console.log('d3.selectAll("#svg-egonets-time-step #all-overviews-g .point")');console.log(d3.selectAll("#svg-egonets-time-step #all-overviews-g .point"));
        this_.lasso = d3Lasso()  // 设置套索参数, 指定目标区域 + 区域内的元素.
                    .closePathSelect(true) 
                    .closePathDistance(100)
                    .items(d3.selectAll("#svg-egonets-time-step #all-overviews-g .point")) // 直接使用d3选择所有的点.               
                    .targetArea(svg);          
         
        let selection = this_.lasso.on("start",function() {  // 监听开始                      
                           this_.lasso.items()
                           .attr("r",1) // reset size
                           .classed("not_possible",true)
                           .classed("selected",false);
                      })
                      .on("draw",function() { // 监听绘制                           
                           this_.isDragLasso = true; // 是否拖动了套素.
                          // Style the possible dots
                           this_.lasso.possibleItems()
                           .classed("not_possible",false)
                           .classed("possible",true);
                          // Style the not possible dot
                            this_.lasso.notPossibleItems()
                            .classed("not_possible",true)
                            .classed("possible",false);
                      })
                      .on("end",function() { // 监听完成.
                          
                          if(this_.isDragLasso){
                            this_.isDragLasso = false;
                            this_.lasso.items()
                            .classed("not_possible",false)
                            .classed("possible",false);
                            // Style the selected dots
                            let selectedDots = this_.lasso.selectedItems()
                              .classed("selected",true)
                              .attr("r",8);                                      
                            let gList = selectedDots._groups[0]; // [g, g, ...]
                            // console.log("selectedDots");console.log(selectedDots);
                            // this_.egoSelectedLassoList.splice(0, this_.egoSelectedLassoList.length); // 清除元素                          
                            d3.selectAll("#svg-egonets-time-step #all-overviews-g .point circle")
                             .attr("stroke", "#d1d1d1")
                             .attr("stroke-width", 1);
                             if(this_.$store.getters.getclickedEgoList.length > 0){
                              this_.$store.getters.getclickedEgoList.forEach(function(d, idx){
                                // 高亮节点
                                 d3.selectAll(".overview-" + d.replace(/\./g, "-"))
                                    .attr("stroke", "#de2d26")
                                    .attr("stroke-width", 2); // 节点边缘颜色为黑色.
                              });
                             }
                            for(let i=0; i < gList.length; i++){
                              let g = gList[i];
                              let className = g.classList[1].split("viewg-")[1]; // viewg-tana-jones
                              // 高亮节点
                              d3.selectAll(".overview-" + className) // overview-hunter-shively
                                .attr("stroke", "#de2d26")
                                .attr("stroke-width", 2); // 节点边缘颜色为黑色.            
                              // this_.egoSelectedLassoList.push(egoId); // ["1224", "3453", ...]
                            }
                          }
                                                  
                          
                      });
        svg.call(selection); // overview-at-timestep     
      },
      egoNetOverview(element, egoPointList, date, dateStringArray){
        /*
        egoPointList: [{ego: 'mao', fvec: [x, x, ...], point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
        */
        let this_ = this;
        let g = d3.select(element);
        let egoPointPosition = {};
        let min_x = d3.min(egoPointList, function(d) {
          let eachPoint = d.point;        
          egoPointPosition[d.ego] = eachPoint; //d.fvec;
          // todo: 在这里构建用于相似性计算的对象,并保存在store.js中.
          return eachPoint[0];
        });
        
        let max_x = d3.max(egoPointList, function(d) {
          let eachPoint = d.point;
          return eachPoint[0];
        });

        let min_y = d3.min(egoPointList, function(d) {
          let eachPoint = d.point;
          return eachPoint[1];
        });

        let max_y = d3.max(egoPointList, function(d) {
          let eachPoint = d.point;
          return eachPoint[1];
        });
        let x = d3.scaleLinear().domain([min_x, max_x]).range([this_.MARGIN, this_.$store.getters.gettimeStepEgonetW - this_.MARGIN]);
        let y = d3.scaleLinear().domain([min_y, max_y]).range([this_.MARGIN, this_.$store.getters.gettimeStepOverviewH - this_.MARGIN]);
        // 颜色映射START
        let val2Color = null;
        // console.log("this_.$store.getters.getattrRadio"); console.log(this_.$store.getters.getattrRadio);
        if(this_.$store.getters.getattrRadio == "position"){
          // val2Color = this_.$store.getters.getcolorMap.pointColorObj;
          val2Color = this_.$store.getters.getcolorMap.pointColorShObj[this_.$store.getters.getcolorRadio];
        }else{
          let minMaxVal = this_.$store.getters.getfilterObj[this_.$store.getters.getattrRadio]; // [min, max]
          let colorList = this_.$store.getters.getcolorSchemeObj[this_.$store.getters.getcolorRadio];
          let colorScheme = [colorList[0], colorList[colorList.length - 1]];        
          val2Color = d3.scaleLinear().domain(minMaxVal)
                            .range(colorScheme);
        }        
        // 颜色映射END
        let enter_points = g.append("g")
                       .attr("class", "overview-points")
                       .selectAll('g')
                       .data(egoPointList)
                       .enter()
                       .append('g')
                       .attr('class', function(d){
                          let egoId = "viewg-" + d.ego; // ego的id, 通常是数字串, 直接使用的话, 是非法类/id名, 需要首字母不为数字.
                          return "point " + egoId.replace(/\./g, "-"); // 效果: mao.tingyun.cher ===> mao-tingyun-cher 
                       })
                       .attr("name", date)
                       .attr('transform', function(d) {
                          return "translate(" + (x(d.point[0])) + "," + (y(d.point[1])) + ")";
                       });
        this_.$store.commit("addOneegoOverviewTimeStepRt", enter_points); // 添加到数组中.
        enter_points.append('circle').attr("r", 3)
                   .attr("class", function(d){
                      let egoId = "overview-" + d.ego; // ego的id, 通常是数字串, 直接使用的话, 是非法类/id名, 需要首字母不为数字.
                      return egoId.replace(/\./g, "-"); // 效果: mao.tingyun.cher ===> mao-tingyun-cher 
                   })
                   .attr("name", function(d){
                      return d.ego;
                   })
                   .attr("fill", function(d){                                    
                       // if(this_.$store.getters.getselectedDataset == "enron"){
                       //   let attrValue = d.egoattrs.position;
                       //   return this_.$store.getters.getcolorMap.pointColorObj[attrValue];
                       // }else{
                       //   return "#d1d1d1";
                       // }
                      let attrVal = d.egoattrs[this_.$store.getters.getattrRadio]; 
                      if(this_.$store.getters.getattrRadio == "position"){                                    
                        return val2Color[attrVal]; 
                      }else{                                                            
                        return val2Color(attrVal);
                      }                                    
                   })
                   .attr("stroke", "#d1d1d1")
                   .attr("stroke-width", 1); // 节点边缘颜色为黑色.

        enter_points.append('text').text(function(d, i) {
          if (this_.$store.getters.getselectedDataset == "enron"){
            return d.egoattrs.name + ": " + d.egoattrs.position;
          }
          else{
            return d.egoattrs.name;
          }          
        })
        .attr('class', function(d){
          let egoId = "txviewg-" + d.ego; // ego的id, 通常是数字串, 直接使用的话, 是非法类/id名, 需要首字母不为数字.
          return egoId.replace(/\./g, "-"); // 效果: mao.tingyun.cher ===> mao-tingyun-cher 
        })
        .attr("name", date)
        .attr('x', 4)
        .attr("display", "none")
        .attr("font-size", 12) // fixme: 中期时加的
        .attr('y', 3);

        enter_points.append('title').text(function(d, i) {          
          if (this_.$store.getters.getselectedDataset == "enron"){
            return d.egoattrs.name + ": " + d.egoattrs.position;
          }
          else{
            return d.egoattrs.name;
          }        
        });
        enter_points.on("mouseover", function(e){                       
                        let egoId = e.ego;
                        let nodeEle = ".viewg-" + egoId.replace(/\./g, "-"); // viewg-mao-ty
                        let lineEle = ".trackline-" + egoId.replace(/\./g, "-"); // tracklineg-tana-jones
                        if(this_.$store.getters.getselectedDataset == "enron"){
                          d3.selectAll("#svg-egonets-time-step #all-overviews-g .point").style('opacity', 0.15);
                          d3.selectAll("#svg-egonets-time-step #track-lines-g .track-line").style('opacity', 0.15);
                          d3.selectAll("#svg-egonets-time-step #all-overviews-g " + nodeEle).style('opacity', 1);
                          d3.selectAll("#svg-egonets-time-step #track-lines-g " + lineEle).style('opacity', 1);
                        }
                        if(this_.$store.getters.getselectedDataset == "tvcg"){
                          d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-" + egoId.replace(/\./g, "-"))
                            .attr("stroke", "#de2d26")
                            .attr("stroke-width", 2); // 节点边缘颜色为黑色.
                        }
                        let circleClass = "dyegovis-" + egoId.replace(/\./g, "-"); 
                        d3.select("#ego-overview-box circle." + circleClass).attr("fill", this_.$store.getters.getcolorMap.egoColor); // overview视图中的对应的节点颜色高亮.                        
                    })
                    .on("mouseout", function(e){  
                      let egoId = e.ego;
                      let circleClass = "dyegovis-" + egoId.replace(/\./g, "-"); 
                      // 颜色映射START
                      let val2Color = null;
                      // console.log("this_.$store.getters.getattrRadio"); console.log(this_.$store.getters.getattrRadio);
                      if(this_.$store.getters.getattrRadio == "position"){
                        // val2Color = this_.$store.getters.getcolorMap.pointColorObj;
                        val2Color = this_.$store.getters.getcolorMap.pointColorShObj[this_.$store.getters.getcolorRadio];
                      }else{
                        let minMaxVal = this_.$store.getters.getfilterObj[this_.$store.getters.getattrRadio]; // [min, max]
                        let colorList = this_.$store.getters.getcolorSchemeObj[this_.$store.getters.getcolorRadio];
                        let colorScheme = [colorList[0], colorList[colorList.length - 1]];        
                        val2Color = d3.scaleLinear().domain(minMaxVal)
                                          .range(colorScheme);
                      }        
                      // 颜色映射END
                      if(this_.$store.getters.getselectedDataset == "enron"){
                        d3.select("#ego-overview-box circle." + circleClass).attr("fill", function(){ // circleClass ="dyegovis-" + egoId.replace(/\./g, "-"); 
                          // this_.$store.getters.getcolorMap.pointColorObj[e.egoattrs.position]
                          let attrVal = e.egoattrs[this_.$store.getters.getattrRadio]; 
                          if(this_.$store.getters.getattrRadio == "position"){                                    
                            return val2Color[attrVal]; 
                          }else{ 
                            // console.log("mouseout val2Color"); console.log(val2Color);                                                           
                            return val2Color(attrVal);
                          }
                        }); // fixme: 中期时加的 
                        d3.selectAll("#svg-egonets-time-step #all-overviews-g .point").style('opacity', 1);
                        d3.selectAll("#svg-egonets-time-step #track-lines-g .track-line").style('opacity', 1);
                      }                      
                      if(this_.$store.getters.getselectedDataset == "tvcg"){
                        d3.select("#ego-overview-box circle." + circleClass).attr("fill", function(){
                          let attrVal = e.egoattrs[this_.$store.getters.getattrRadio];
                          return val2Color(attrVal);
                        }); // fixme: 中期时加的 
                        if(this_.$store.getters.getclickedEgoList.indexOf(egoId) == -1){
                          d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-" + egoId.replace(/\./g, "-"))
                            .attr("stroke", "#d1d1d1")
                            .attr("stroke-width", 1);
                        }
                      } 
                    });
        enter_points.on('click', function(d, i) {
          let egoId = d.ego;
          if(this_.$store.getters.getclickedEgoList.indexOf(egoId) == -1){ // 没有点击过. 
            ///////显示对应的egonet序列////////
            if(this_.$store.getters.getselectedEgoList.indexOf(egoId) == -1){ // 说明不在里面.
              this_.$store.commit("changeselectedEgoList", egoId); // 首先添加到store.js中的selectedEgoList=["ego1", "ego2", ...]              
              if(this_.$store.getters.getselectedDataset == "enron"){
                bus.$emit("selectDynamicEgonet", [egoId, d.egoattrs.name + ": " + d.egoattrs.position]); // 发射信号,触发响应 
              }else{
                bus.$emit("selectDynamicEgonet", [egoId, d.egoattrs.name]); // 发射信号,触发响应 
              }        
              let newEgoId = "dyegovis-" + egoId; // "dyegovis-1234", "dyegovis-mao.mty"
              let addnewEgoId = newEgoId.replace(/\./g, "-");
              d3.select("#ego-overview-box circle." + addnewEgoId).attr("stroke", "#de2d26").attr("stroke-width", 1); // 用黑圈高亮选中的点.
              d3.select("#ego-overview-box text." + addnewEgoId).attr("display", "block"); // 显示标签.
            }         
            ///////////////
            this_.$store.commit("changeclickedEgoList", egoId);
            let element = ".viewg-" + egoId.replace(/\./g, "-"); // viewg-mao-ty
            let allNodeg = d3.selectAll(element)._groups[0]; // [g, g, ...]                      
            let linkEgo = []; // [{source: [x, y], target: [x, y]}, ...]
            for(let i=0; i<allNodeg.length - 1; i++){
              let dateNodeS = allNodeg[i].attributes.name.nodeValue; // egonet所属的时间步.
              let transformS = allNodeg[i].attributes.transform.nodeValue; // "translate(32.62172835813489,121.06306996960215)"
              let posListS = transformS.split(","); // ["translate(32.62172835813489", "121.06306996960215)"]
              let obj = {};
              obj.source = [parseFloat(posListS[0].split("(")[1]) + this_.$store.getters.gettimeStepEgonetW * this_.$store.getters.getdateStringArray.indexOf(dateNodeS), parseFloat(posListS[1].split(")")[0])];
              let dateNodeT = allNodeg[i + 1].attributes.name.nodeValue;
              let transformT = allNodeg[i + 1].attributes.transform.nodeValue; // "translate(32.62172835813489,121.06306996960215)"
              let posListT = transformT.split(","); // ["translate(32.62172835813489", "121.06306996960215)"]
              obj.target = [parseFloat(posListT[0].split("(")[1]) + this_.$store.getters.gettimeStepEgonetW * this_.$store.getters.getdateStringArray.indexOf(dateNodeT), parseFloat(posListT[1].split(")")[0])];
              linkEgo.push(obj); // [{source: x, target: x}, ...]
            }            
            let enter_lines = d3.select("#svg-egonets-time-step #track-lines-g") // 节点之间的线段.
                     .append("g")
                     .attr("class", function(){
                        return "tracklineg-" + egoId.replace(/\./g, "-"); // trackline-mao-ty 
                     })
                     .selectAll('line')
                     .data(linkEgo) // [{source: [x, y], target: [x, y]}, ...]
                     .enter()
                     .append('line')
                     .attr('class', function(d, index){
                        return "track-line trackline-" + egoId.replace(/\./g, "-"); // trackline-mao-ty
                     })
                     .attr("stroke", function(){
                       let idx = this_.$store.getters.getselectedEgoList.indexOf(egoId);
                       let color = this_.$store.getters.getcolorSchemeList[idx];
                       return color;
                     }) // "#de2d26":                                      
                     .attr("stroke-width", 2);           
            enter_lines.attr("x1", function (d) { return d.source[0]; })
                            .attr("y1", function (d) {return d.source[1];})
                            .attr("x2", function (d) {
                              return d.target[0];                            
                            })
                            .attr("y2", function (d) {
                              return d.target[1];                            
                            });
            // 高亮节点
            d3.selectAll(".overview-" + egoId.replace(/\./g, "-"))
              .attr("stroke", function(){
                 let idx = this_.$store.getters.getselectedEgoList.indexOf(egoId);
                 let color = this_.$store.getters.getcolorSchemeList[idx];
                 return color;
              }) // "#de2d26"
              .attr("stroke-width", 2); // 节点边缘颜色为黑色.
            

          }else{ // 已经点击过一次了.
            d3.select(".tracklineg-" + egoId.replace(/\./g, "-")).remove();          
            let index = this_.$store.getters.getclickedEgoList.indexOf(egoId);            
            this_.$store.commit("removeOneclickedEgoList", index);            
            d3.selectAll(".overview-" + egoId.replace(/\./g, "-"))
              .attr("stroke", "#d1d1d1")
              .attr("stroke-width", 1); // 节点边缘颜色为黑色.
          }                           
      }); 

     }     
    },
    created(){
      let this_ = this;
      bus.$on("getOverviewTimeSteps", function(data){
        let selectedTimestepNum_ = this_.getTimestepNum();        
        this_.addOverviewTimeStep(selectedTimestepNum_);      
        this_.drawOverviewTimestep(data);
      });
    },
    mounted(){
      let this_ = this; 
      // this_.eventInit();    
      this_.jBoxInstance.egosnpDetail = new jBox("Modal", {
            id: "jBox-egonetsnpinfo",
            addClass: "jBox-egonetsnpinfo",  // 添加类型,这个功能很棒啊!
            attach: '.egonetsnpOVContextMenu',  // 这是历史走廊的图标.点击这个图标打开历史走廊弹窗.
            maxWidth: 200,            
            maxHeight: 550,
            // adjustTracker:true,
            title: 'Egonet Snapshot Details',
            overlay: false,
            zIndex: 1005, // fixme:注意多个jBox实例之间zIndex的值决定与最后一个实例.
            createOnInit: true,
            content: $("#overview-egonetsnp-info"),  // jQuery('#jBox-content') 
            draggable: true,
            repositionOnOpen: false,
            repositionOnContent: true,    
            // target: $('#egonets-time-step'),
            offset: {x: -110, y: -60},            
            onCloseComplete: function(){
               // let egoId = this_.curViewEgo;
               // let pointSt = "#egonets-time-step .overview-points .point circle[name='" + this_.curViewEgo + "']";
               let pointSt = "#egonets-time-step .overview-points .point[name='" + this_.curTimeStep + "'] circle[name='" + this_.curViewEgo + "']";
               d3.select(pointSt).attr("stroke", "#d1d1d1").attr("stroke-width", 1); // 高亮点. 
               this_.curViewEgo = null;
               this_.curTimeStep = null;       
            }
      });
      this_.contextMenuForSnp();        
    },
    updated(){
      console.log("egoOverviewTimeStep updated");
    },
    beforeDestroy(){
      console.log("egoOverviewTimeStep beforeDestroy");
      // bus.$off("refreshMDSLayout");
      bus.$off("getOverviewTimeSteps");
    }
  }
</script>
<style> 
  
</style>