<template>		    
	 <div id="ego-overview">
     <div id="ego-overview-box">
        <!-- <div id="tool-for-overview">          
            <div class="overview-filter-box">
              <img class="overview-img-icon" id="overview-filter-icon-img" width="15" height="15" src="../../static/img/filter.svg">
            </div>
            <div class="overview-legend-box">
              <img class="overview-img-icon" id="overview-legend-icon-img" width="15" height="15" src="../../static/img/legend.svg">
            </div>
            <div class="overview-vis-box">
              <img class="overview-img-icon" id="overview-vis-icon-img" width="15" height="15" src="../../static/img/novis.svg">
            </div>          
        </div> -->        
        <!-- <div id="overview-for-legend"></div> -->
        <div id="overview-dyegonet-info"></div>
     </div>
   </div>		
</template>

<script>
  // eslint-disable-next-line
  /* eslint-disable */
  import * as d3 from '../../static/js/d3.v4.min.js'
  import '../../static/js/numeric.min.js'  
  import {vueFlaskRouterConfig} from '../flaskRouter'
  import bus from '../eventbus.js' // 事件总线.
  import axios from 'axios'  
  import {d3Lasso} from "../../static/js/lasso.js"
  // import $ from 'jquery'
  import * as $ from "../../static/js/jquery.min.js" // 使用外部引入的方式才能使用jBox.js
  import {jBox} from "../../static/js/jBox.js"
  import $$ from 'jquery'
  import "../../static/js/jquery.contextMenu.js"
  import "../../static/js/jquery.ui.position.js" 

  export default {    
    data(){
      return {
        svg: null,
        svgWidth: 525,
        svgHeight: 500,
        MARGIN: 20, // 画布空白设置.
        pointColor: "#a7a7a7", // 点的颜色 #FF8700
        egoSelectedLassoList: [], // [egoId, ...]
        zoomHandler: null,
        lasso: null,
        jBoxInstance:{ // 弹出窗口
          // filter: null,
          // legend: null,
          egoDetail: null
        },
        isShowEdges: false, // 是否展示egos间的边.
        curViewEgo: null // 当前选中查看细节的点.
      }
    },
    computed: {

    },
    watch: {
      
    },
    components: {
     
    },
    methods:{
    getStatDiagramForDetail(dbname, selector, egoInfoObj, barWidth, barHeight, svgHeight){ // 在细节框中生成小的统计图.
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
      // ['Degree', 'Density', 'Avg_weight', 'num_edges_alters', 'num_2_alters', 'avg_alters_alters'];
      let barMargin = 2; 
      for(let idx=0; idx < egoInfoObj.ftList.length; idx++){
        let ftName = egoInfoObj.ftList[idx];
        // 接下来取出对应的信息, 构建DOM.
        let ftValList = egoInfoObj.info.features[ftName]; // 取出该特征序列值.
        let sliceStartIdx = 0; // 时间区间的起始位置.
        let sliceEndIdx = this_.$store.getters.gettimeStepList.length - 1;
        if(this_.$store.getters.gettimeStepSlice.length > 0){
          sliceStartIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);
          sliceEndIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[1]);
        }
        // 
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
           .append("title")
           .attr("class", "bart")
           .text(function(){
              let timestep = this_.$store.getters.gettimeStepList[sliceStartIdx + i];              
              return "T: " + timestep + ", Val: " + newftValList[i].toFixed(2);
           });
        }
      }
      egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
          return "Timespan: " + this_.$store.getters.gettimeStepSlice[0] + " - " + this_.$store.getters.gettimeStepSlice[1];
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
        let sliceStartIdx = 0; // 时间区间的起始位置.
        let sliceEndIdx = this_.$store.getters.gettimeStepList.length - 1;
        if(this_.$store.getters.gettimeStepSlice.length > 0){
          sliceStartIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);
          sliceEndIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[1]);
        }
        let ftValList = egoInfoObj.info.p_num_year;
        let newftValList = ftValList.slice(sliceStartIdx, sliceEndIdx + 1); // [x, x, x, ...]
        let maxVal = Math.max(...newftValList);
        // let minVal = Math.min(...newftValList);
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
           .attr("class", "ftbar")
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
    getDyEgonetInfo(egoId){
      let this_ = this;
      let dbname = this_.$store.getters.getselectedDataset;
      let selector = "#overview-dyegonet-info"; 
      let barWidth = 4;
      let barHeight = 12;
      let svgHeight = 13;
      let param = {dbname: dbname, egoId: egoId};
        axios.post(vueFlaskRouterConfig.dyegonetDetail, {
          param: JSON.stringify(param)
      })
      .then((res) => {
          let egoInfoObj = res.data;
          // console.log("getDyEgonetInfo egoInfoObj");console.log(egoInfoObj);
          this_.getStatDiagramForDetail(dbname, selector, egoInfoObj, barWidth, barHeight, svgHeight);
        })
      .catch((error) => {            
        console.error(error);
      });
    },
    contexMenuEvents(){
      let this_ = this;
      $$.contextMenu({ 
        // fixme: contextMenu插件是一个事件类型的,也就是说,mounted阶段并没有'each-dyegonet-bg'这个元素,需要点击ego后才能渲染出来,但是由于这是一个事件,则直接在mounted里面注册,一旦出现这样的元素则会直接绑定到上面,在这些元素上右键点击触发对应事件.
        selector: '#ego-overview .point', // 绑定的元素,当在该元素右键时,就会弹出右键选择项目. 验证去掉背景矩形.
        // selector: '.each-dyegonet', // 绑定的元素,当在该元素右键时,就会弹出右键选择项目.
        className: "dyegonetOVContextMenu",
        callback: function(key, options) {               
           let egoId = options.$trigger[0].childNodes[0].attributes[2].nodeValue; // 该dyegonet的ego的ID.
           if(key == "delete"){  // 如果点击的是"delete"选项.               
             // console.log("contexMenuEvents options");console.log(options.$trigger[0].childNodes[0].attributes[2].nodeValue);             
             this_.jBoxInstance.egoDetail.open();
             this_.getDyEgonetInfo(egoId);
             let pointSt = null;
             if(this_.curViewEgo){
               pointSt = "#svg-ego-overview .everything .point circle[name='" + this_.curViewEgo + "']";
               d3.select(pointSt).attr("stroke", "#d1d1d1").attr("stroke-width", 1);
             }
             
             pointSt = "#svg-ego-overview .everything .point circle[name='" + egoId + "']";
             d3.select(pointSt).attr("stroke", "black").attr("stroke-width", 2); // 高亮点.
             this_.curViewEgo = egoId;
           }
           if(key == "copy"){
              let newEgoId = "dyegovis-" + egoId; // "dyegovis-1234", "dyegovis-mao.mty"
              let addnewEgoId = newEgoId.replace(/\./g, "-");              
              d3.select("#ego-overview-box text." + addnewEgoId).attr("display", "block"); // 显示标签.
           }
           if(key == "edit"){
              let newEgoId = "dyegovis-" + egoId; // "dyegovis-1234", "dyegovis-mao.mty"
              let addnewEgoId = newEgoId.replace(/\./g, "-");              
              d3.select("#ego-overview-box text." + addnewEgoId).attr("display", "none"); // 显示标签.
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
    tooltipForOverview(){
      let this_ = this;      
      // $(".overview-legend-box").jBox("Mouse", { ///
      //     theme: 'TooltipDark',
      //     content: 'See legend',
      //     position: {
      //       x: 'left',
      //       y: 'bottom'
      //    }
      // });
      $(".overview-vis-box").jBox("Mouse", { ///
          theme: 'TooltipDark',
          content: 'Show edges',
          position: {
            x: 'left',
            y: 'bottom'
         }
      });
     },
     eventInit(){
      let this_ = this;
      d3.select("#overview-vis-icon-img").on("click", function(){
        //isShowEdges
        if(this_.isShowEdges){ // true
            this.setAttribute("src", "../../static/img/novis.svg");
            this_.isShowEdges = false;
            // d3.selectAll("#svg-ego-time-curve " + "line").style('display', "none");
         }else{ // false
            this.setAttribute("src", "../../static/img/vis.svg");
            this_.isShowEdges = true;
            // d3.selectAll("#svg-ego-time-curve " + "line").style('display', "block");
         }
      });
      $(window).on('keydown', function (evt){ // 按下shift时, 取消缩放功能 + 开启监听套索功能.
        
        if(evt.key.toLowerCase() == "shift"){
          // console.log("keydown");console.log(evt.key);
          this_.svg.on('.zoom', null); // 放大失能
          let selection = this_.lasso.on("start",function() {  // 监听开始                      
                        this_.lasso.items()
                             .attr("r",6) // reset size
                             .classed("not_possible",true)
                             .classed("selected",false);
                    })
                    .on("draw",function() { // 监听绘制

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
                        // Reset the color of all dots
                        this_.lasso.items()
                            .classed("not_possible",false)
                            .classed("possible",false);

                        // Style the selected dots
                        let selectedDots = this_.lasso.selectedItems()
                            .classed("selected",true)
                            .attr("r",8);                                      
                        let gList = selectedDots._groups[0]; // [g, g, ...]
                        this_.egoSelectedLassoList.splice(0, this_.egoSelectedLassoList.length); // 清除元素
                        // d3.selectAll("#ego-overview-box .point circle").attr("stroke", "#d1d1d1").attr("stroke-width", 2); //先消除所有的高亮.
                        for(let i=0; i < gList.length; i++){
                          let g = gList[i];                                                   
                          let egoId = g.children["0"].attributes[2].nodeValue; // 取出节点的name属性的值, 即ego对应的id.
                          // let egoName = g.children[2].innerHTML.split(":")[0]; // richard.ring: Employee   
                          let egoName = g.children[2].innerHTML; // richard.ring: Employee  
                          // console.log("egoName");console.log(egoName);                      
                          this_.egoSelectedLassoList.push([egoId, egoName]); // ["1224", "3453", ...]                         
                          d3.select("#ego-overview-box circle." + "dyegovis-" + egoId.replace(/\./g, "-")).attr("stroke", function(){
                             let idx = this_.$store.getters.getselectedEgoList.indexOf(egoId);
                             let color = this_.$store.getters.getcolorSchemeList[idx];
                             return color;
                          }); // .attr("stroke-width", 2)
                        }
                        // console.log("this_.egoSelectedLassoList");console.log(this_.egoSelectedLassoList);
                        for(let i=0; i < this_.egoSelectedLassoList.length; i++){
                           let selectedEgoId = this_.egoSelectedLassoList[i][0];
                           let selectedEgoName = this_.egoSelectedLassoList[i][1];
                           if(this_.$store.getters.getselectedEgoList.indexOf(selectedEgoId) == -1){ // 说明不在里面.
                              this_.$store.commit("changeselectedEgoList", selectedEgoId); // 首先添加到store.js中的selectedEgoList=["ego1", "ego2", ...]
                              bus.$emit("selectDynamicEgonet", [selectedEgoId, selectedEgoName]); // 发射信号,触发响应
                           }
                        }
                        
                    });
          this_.svg.call(selection);
        }
      });
      $(window).on('keyup', function (evt){ // 放开shift时,恢复缩放功能 + 取消套索.
        
        if(evt.key.toLowerCase() == "shift"){
          // console.log("keyup");console.log(evt.key);
          this_.zoomHandler(this_.svg);
          let selection = this_.lasso.on(".dragstart", null)
                                     .on(".drag", null)
                                     .on(".dragend", null);
          this_.svg.call(selection);
        }         
        
      });
     },     
     egoNetOverview(egoPointList){
      /*
      egoPointList: [{ego: 'mao', fvec: [x, x, ...], point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]
      */
      let this_ = this; 
      // 颜色映射START
      let val2Color = null;
      // console.log("this_.$store.getters.getattrRadio egoNetOverview"); console.log(this_.$store.getters.getattrRadio);
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
      d3.select("#svg-ego-overview").remove(); // 清除svg中旧的内容.      
      this_.svg = d3.select("#ego-overview-box").append("svg")
                    .attr("id", "svg-ego-overview")
                    .attr("width", this_.svgWidth)
                    .attr("height", this_.svgHeight);
      // 在svg的左上角添加一些文本信息      
      let textInfo = this_.svg.append("g")
                          .attr("class", "dyegonet-info");
      textInfo.append("text").attr("class", "egonet-infotext").text(function(){
        return "Number of points:" + egoPointList.length; 
      })
      // .attr("style", "font-size:13px;opacity: 0.8")
      .attr("x", 1)
      .attr("y", 12);
      let g = this_.svg.append("g")
                 .attr("class", "everything");
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
      this_.$store.commit("changeegoPointPosition", egoPointPosition);
      let x = d3.scaleLinear().domain([min_x, max_x]).range([this_.MARGIN, this_.svgWidth - this_.MARGIN]);
      // let y = d3.scaleLinear().domain([min_y, max_y]).range([this_.svgHeight - this_.MARGIN, this_.MARGIN]); 
      let y = d3.scaleLinear().domain([min_y, max_y]).range([this_.MARGIN, this_.svgHeight - this_.MARGIN]);   
      /*
        备注: 浏览器都是以一个div的左上角为坐标原点来确定像素位置的, 而这里的坐标指的是绘制散点图的时候参考的坐标.
        1). X: domain([小, 大]).range([小, 大]); Y: domain([小, 大]).range([小, 大]) ==> 以左上角为坐标原点画散点图.
        2) X: domain([小, 大]).range([大, 小]); Y: domain([小, 大]).range([小, 大]) ==> 以右上角为坐标原点画散点图.
        3) X: domain([小, 大]).range([小, 大]); Y: domain([小, 大]).range([大, 小]) ==> 以左下角为坐标原点画散点图.
        4) X: domain([小, 大]).range([大, 小]); Y: domain([小, 大]).range([大, 小]) ==> 以右下角为坐标原点画散点图.
      */

      let enter_points = g.selectAll('.point').data(egoPointList)
                     .enter()
                     .append('g')
                     .attr('class', 'point')
                     .attr('transform', function(d) {
                        return "translate(" + (x(d.point[0])) + "," + (y(d.point[1])) + ")";
                     });
      
      enter_points.append('circle').attr("r", 6)
                                   .attr("class", function(d){
                                      let egoId = "dyegovis-" + d.ego; // ego的id, 通常是数字串, 直接使用的话, 是非法类/id名, 需要首字母不为数字.
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
                                   .attr("stroke-width", function(){
                                      // if(this_.$store.getters.getselectedDataset == "tvcg"){
                                      //   return 1;
                                      // }else{
                                      //   return 2;
                                      // }
                                      return 1;
                                   }); // 节点边缘颜色为黑色.

      enter_points.append("text")  // 显示节点的标签.
        .text(function(d) { 
            // console.log("enter_points dddddd");console.log(d);                                         
            if(this_.$store.getters.getselectedDataset == "enron"){
              return d.egoattrs.name + "(" + d.egoattrs.position + ")";
            }
            if(this_.$store.getters.getselectedDataset == "tvcg"){
              return d.egoattrs.name;
            }                                         
        })
        .attr("class", function(d){
            let egoId = "dyegovis-" + d.ego; // ego的id, 通常是数字串, 直接使用的话, 是非法类/id名, 需要首字母不为数字.
            return egoId.replace(/\./g, "-"); // 效果: mao.tingyun.cher ===> mao-tingyun-cher 
         })
        .attr('x', 8)
        .attr("display", "none")
        .attr("font-size", 11) // fixme: 中期时加的
        .attr('y', 3);

      enter_points.append('title').text(function(d, i) {
        if (this_.$store.getters.getselectedDataset == "enron"){
          return d.egoattrs.name + ": " + d.egoattrs.position;
        }else{
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
                  })
                  .on("mouseout", function(e){  
                    let egoId = e.ego;
                    if(this_.$store.getters.getselectedDataset == "enron"){
                      d3.selectAll("#svg-egonets-time-step #all-overviews-g .point").style('opacity', 1);
                      d3.selectAll("#svg-egonets-time-step #track-lines-g .track-line").style('opacity', 1);
                    }                      
                    if(this_.$store.getters.getselectedDataset == "tvcg"){                    
                      if(this_.$store.getters.getclickedEgoList.indexOf(egoId) == -1){
                          d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-" + egoId.replace(/\./g, "-"))
                            .attr("stroke", "#d1d1d1")
                            .attr("stroke-width", 1);
                      }
                    } 
                  });

      enter_points.on('click', function(d, i) {
        let egoId = d.ego; // mao.ty     
        if(this_.$store.getters.getselectedEgoList.indexOf(egoId) == -1){ // 说明不在里面.
          this_.$store.commit("changeselectedEgoList", egoId); // 首先添加到store.js中的selectedEgoList=["ego1", "ego2", ...]
          if(this_.$store.getters.getselectedDataset == "enron"){
            bus.$emit("selectDynamicEgonet", [egoId, d.egoattrs.name + ": " + d.egoattrs.position]); // 发射信号,触发响应 
          }else{
            bus.$emit("selectDynamicEgonet", [egoId, d.egoattrs.name]); // 发射信号,触发响应 
          }                   
          let newEgoId = "dyegovis-" + egoId; // "dyegovis-1234", "dyegovis-mao.mty"
          let addnewEgoId = newEgoId.replace(/\./g, "-");
          d3.select("#ego-overview-box circle." + addnewEgoId).attr("stroke", function(){
             // let idx = this_.$store.getters.getselectedEgoList.indexOf(egoId);
             // let color = this_.$store.getters.getcolorSchemeList[idx];
             // return color;
             return "#de2d26";
          }).attr("stroke-width", 1); // 用黑圈高亮选中的点.
          d3.select("#ego-overview-box text." + addnewEgoId).attr("display", "block"); // 显示标签.
        }
        if(this_.$store.getters.getclickedEgoList.indexOf(egoId) == -1){ // 没有点击过.            
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
                   })                                         
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
            })
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
      this_.zoomHandler = d3.zoom()
                          .scaleExtent([0.5, 25]) // zoom range
                          .on("zoom", updateOverview);
      this_.zoomHandler(this_.svg);
      function updateOverview(){         
        let newX = d3.event.transform.rescaleX(x);
        let newY = d3.event.transform.rescaleY(y);
        g.selectAll('.point')                        
         .attr('transform', function(d) {
          return "translate(" + (newX(d.point[0])) + "," + (newY(d.point[1])) + ")";
        });                                      
      }                   
      this_.svg.on("dblclick.zoom", null); // fixme:失能双击放大.      
      this_.lasso = d3Lasso()  // 设置套索参数, 指定目标区域 + 区域内的元素.
                    .closePathSelect(true) 
                    .closePathDistance(100)
                    .items(enter_points)
                    .targetArea(this_.svg);
      this_.$store.commit("changeegoOverviewRt", enter_points);
     }     
    },
    created(){
      console.log("created");
      let this_ = this;
      bus.$on('getEgoVecObj', function (data){
        // [{ego: 'mao', point: [x, y], egoattrs: {attr1: x, attr2: x, ...}}, ...]        
        this_.egoNetOverview(data); //data.egopointlist, data.egolist); // data.egopointlist: [[x, y], ...], data.egolist: ['a', 'b', ...]      
      }); 
    },
    mounted(){
      console.log("egoOverview mounted");
      let this_ = this;
      // this_.tooltipForOverview();
      this_.eventInit();
      this_.tooltipForOverview();
      this_.jBoxInstance.egoDetail = new jBox("Modal", {
            id: "jBox-dyegonetinfo",
            addClass: "jBox-dyegonetinfo",  // 添加类型,这个功能很棒啊!
            attach: '.dyegonetOVContextMenu',  // 这是历史走廊的图标.点击这个图标打开历史走廊弹窗.
            maxWidth: 200,            
            maxHeight: 550,
            // adjustTracker:true,
            title: 'Dynamic Egonet Details',
            overlay: false,
            zIndex: 1005, // fixme:注意多个jBox实例之间zIndex的值决定与最后一个实例.
            createOnInit: true,
            content: $("#overview-dyegonet-info"),  // jQuery('#jBox-content') 
            draggable: true,
            repositionOnOpen: false,
            repositionOnContent: true,    
            target: $('#ego-overview-box'),
            offset: {x: 130, y: -210},            
            onCloseComplete: function(){
               // let egoId = this_.curViewEgo;
               let pointSt = "#svg-ego-overview .everything .point circle[name='" + this_.curViewEgo + "']";
               d3.select(pointSt).attr("stroke", "#d1d1d1").attr("stroke-width", 1); // 高亮点. 
               this_.curViewEgo = null;          
            }
      });
      this_.contexMenuEvents();     
    },
    updated(){
      console.log("egoOverview updated");
    },
    beforeDestroy(){
      console.log("egoOverview beforeDestroy");
      bus.$off("getEgoVecObj"); // getOverviewTimeSteps
    }   
  }
</script>

<style>
  #ego-overview-box {
    width: 525px;
    height: 500px;
    background: 0;
    border: 1px solid #aaaaaa;
    border-top-width: 1px;
    border-right-width: 1px;
    border-bottom-width: 1px;
    border-left-width: 1px;
    position: relative;
  }
  #tool-for-overview{
    width: 60px;
    height:18px;
    position:absolute;
    top:2px;
    right:2px;
    border: 1px solid #aaaaaa;
    border-top-width: 1px;
    border-right-width: 1px;
    border-bottom-width: 1px;
    border-left-width: 1px;
    display: flex;
    justify-content: space-around;
  }
  #svg-ego-overview {
    background: 0;    
  }
  
  /* lasso */
.lasso path {
  stroke: rgb(80,80,80);
  stroke-width:2px;
}

.lasso .drawn {
  fill-opacity:.05 ;
}

.lasso .loop_close {
  fill:none;
  stroke-dasharray: 4,4;
}

.lasso .origin {
  fill:#3399FF;
  fill-opacity:.5;
}

/*.not_possible {
  fill: rgb(200,200,200);
}*/

.possible {
  fill: #EC888C;
}

/*.selected {
  fill: steelblue;
}*/
</style>