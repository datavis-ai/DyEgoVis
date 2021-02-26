<template>		    
	 <div id="time-curve-view-div">
     <div id="time-curve-view">       
       <div id="tool-for-timecurve">          
          <div id="legend-icon-box">
            <img class="timecurve-img-icon" id="legend-icon-img" width="16" height="16" src="../../static/img/legend.svg">
          </div>
          <div id="vis-icon-box">
            <img class="timecurve-img-icon" id="vis-icon-img" width="16" height="16" src="../../static/img/novis.svg">
          </div>          
       </div>
     </div>
     <div id="timecurve-legend-box"></div>
     <div id="overview-egonetst-info"></div>   
   </div>   		
</template>

<script>
  // eslint-disable-next-line
  /* eslint-disable */
  import * as d3 from '../../static/js/d3.v4.min.js'
  import {BubbleSet, BSplineShapeGenerator, ShapeSimplifier, PointPath} from '../../static/js/bubblesets.js'
  import {vueFlaskRouterConfig} from '../flaskRouter'
  import bus from '../eventbus.js' // 事件总线.
  import axios from 'axios'
  import {mapGetters} from "vuex"
  import * as chroma from '../../static/js/chroma.min.js'
  // import { mapState } from 'vuex'
  import * as $ from "../../static/js/jquery.min.js"
  import $$ from 'jquery'
  import {jBox} from "../../static/js/jBox.js"
  import "../../static/js/jquery.contextMenu.js"
  import "../../static/js/jquery.ui.position.js"

  export default {    
    data(){
      return {
        svgWidth: 525,
        svgHeight: 376,
        MARGIN: 20, // 画布空白设置.
        stateNodeR: 4, // 节点大小
        isVisLine: false, // 状态之间的连线是否可见
        // isClickNode: false, // 是否点击了节点.
        colorChangeList: [["#FFCCFF", "#FF0000"], ["#FFFF99", "#FF9900"], ["#CCFFFF", "#CCCC00"], ["#99FFFF", "#999900"], ["#6666FF", "#660000"]], // fixme: 中期时加的
        jBoxInstance: {                
          legendJbox: null, // 图例. jBoxInstance.legendJbox
          egosnpDetail: null
        },
        curViewEgo: null,
        curTimeStep: null,
        order: null
      }
    },
    computed: {
       ...mapGetters([
         "getselectedEgoList"
        ])
    },
    watch: {
      getselectedEgoList: function(curVal, oldVal){
        let this_ = this;
        // console.log("timeCurveView getselectedEgoList");
        // console.log(curVal);
        d3.select("#svg-ego-time-curve").remove(); // 清除svg中旧的内容.
        d3.selectAll(".color-legend-item").remove();
        bus.$emit("startStackedG", true);
        if(curVal.length > 0){
          // if(oldVal.length >= 0){
          let timeInterval = this_.$store.getters.gettimeStepSlice; // [2000-02, 2002-01]
          let timeStepList = this_.$store.getters.gettimeStepList; // [x, x, ...]
          if(timeStepList[0] == timeInterval[0] && timeStepList[timeStepList.length - 1] == timeInterval[1]){
             timeInterval = [];
          }       
          let param = {dbname: this_.$store.getters.getselectedDataset, timeInterval: timeInterval, selectedegolist: curVal, whichDistance: this_.$store.getters.getselectedDistance, whichMethodRD: this_.$store.getters.getselectedMethodRD};
          axios.post(vueFlaskRouterConfig.getalltimecurves, {
            param: JSON.stringify(param)
          })
          .then((res) => {
              // console.log("res.data cher");console.log(res.data);                  
              this_.egoNetTimeCurves(res.data);  // timeCurveObj: {ego1: {"2000-08": {"point": [x, y], "feature_vec": []}, "2000-09": {}}, ...}
            })
          .catch((error) => {            
            console.error(error);
          });
        }
        
      }
    },
    components: {
     
    },
    methods:{
      getStatDiagramForDetail(dbname, selector, egoInfoObj, barWidth, barHeight, svgHeight, curTimeStep, egoId){
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
                return this_.$store.getters.getcolorSchemeList[this_.$store.getters.getselectedEgoList.indexOf(egoId)];
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
                return this_.$store.getters.getcolorSchemeList[this_.$store.getters.getselectedEgoList.indexOf(egoId)];
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
        let selector = "#overview-egonetst-info"; 
        let barWidth = 4;
        let barHeight = 12;
        let svgHeight = 13;        
        let param = {dbname: dbname, egoId: egoId};
          axios.post(vueFlaskRouterConfig.dyegonetDetail, {
            param: JSON.stringify(param)
        })
        .then((res) => {
            let egoInfoObj = res.data;            
            this_.getStatDiagramForDetail(dbname, selector, egoInfoObj, barWidth, barHeight, svgHeight, curTimeStep, egoId);
          })
        .catch((error) => {            
          console.error(error);
        });
      },
      contextMenuForSnp(){
        let this_ = this;
        $$.contextMenu({ 
          // fixme: contextMenu插件是一个事件类型的,也就是说,mounted阶段并没有'each-dyegonet-bg'这个元素,需要点击ego后才能渲染出来,但是由于这是一个事件,则直接在mounted里面注册,一旦出现这样的元素则会直接绑定到上面,在这些元素上右键点击触发对应事件.
          selector: '#timecurveview .ego-time-curve .time-steps-points .point', // 绑定的元素,当在该元素右键时,就会弹出右键选择项目. 验证去掉背景矩形.
          // selector: '.each-dyegonet', // 绑定的元素,当在该元素右键时,就会弹出右键选择项目.
          className: "egonetstOVContextMenu",
          callback: function(key, options) {               
             if(key == "delete"){  // 如果点击的是"delete"选项.               
               // console.log("contexMenuEvents options");console.log(options.$trigger[0].childNodes[0].attributes[2].nodeValue);
               // console.log("contexMenuEvents options"); console.log(options);
               let egoId = options.$trigger[0].__data__.ego; // 该dyegonet的ego的ID.
               let curTimeStep = options.$trigger[0].__data__.time_step;
               let order = options.$trigger[0].__data__.order;
               this_.jBoxInstance.egosnpDetail.open();               
               this_.getDyEgonetSnpInfo(egoId, curTimeStep);
               let pointSt = null;
               if(this_.curViewEgo){
                 pointSt = '#timecurveview .ego-time-curve .time-steps-points .point' + " .node-" + this_.curViewEgo.replace(/\./g, "-") + "-" + this_.order;
                 d3.select(pointSt).attr("stroke", "#d1d1d1").attr("stroke-width", 1);
               }               
               pointSt = '#timecurveview .ego-time-curve .time-steps-points .point' + " .node-" + egoId.replace(/\./g, "-") + "-" + order;
               d3.select(pointSt).attr("stroke", "black").attr("stroke-width", 2); // 高亮点.
               this_.curViewEgo = egoId;
               this_.curTimeStep = curTimeStep;
               this_.order = order;
             }           
          },
          items: {
              "delete": {name: "View Details"},
              // "copy": {name: "Delete all"},
              "quit": {name: "Quit"}
          },
          zIndex: 1200
        });
      },
      debounce(func, delay) {
        let timeout=null;
        return function() {        
            if(timeout) clearTimeout(timeout);
            let context = this, args = arguments;       
            timeout = setTimeout(function(){          
              func.apply(context, args);
            },delay);
        };
      },
      mergeArrays(){
        return Array.prototype.concat.apply([], arguments);
      },
      createPathLayer(element, color, dAttr){
        // let path = document.createElement("path");
        // path.setAttribute("opacity", 0.5); // <path id="path" opacity="0.5" stroke="black"></path>
        // path.setAttribute("fill", color); // <path id="path" opacity="0.5" stroke="black"></path>
        // path.setAttribute("d", dAttr);
        element.append("path") // 绘制出轮廓线.
               .attr("opacity", 0.3)
               .attr("fill", color)
               .attr("d", dAttr)
      },
      getOutline(innerPointList, outerPointList, pad) { // 获得bubbleSet的轮廓.
        let bubbles = new BubbleSet();
        let list = bubbles.createOutline( // 创建轮廓 (members, nonmem, edges)
          BubbleSet.addPadding(innerPointList, pad), // 包含的点 rectanglesA=[{x: x, y: x, width: x, height: x}, ...]
          BubbleSet.addPadding(outerPointList, pad), // 不包含的点
          null
        ); // 轮廓的点列表
        let outline = new PointPath(list).transform([ // PointPath(_points)
          new ShapeSimplifier(0.0),
          new BSplineShapeGenerator(),
          new ShapeSimplifier(0.0),
        ]);
        return outline.toString(); // 转化成path元素的d属性.
      },
      tooltipForOverview(){
        let this_ = this;        
        $("#legend-icon-box").jBox("Mouse", { ///
            theme: 'TooltipDark',
            content: 'See legend',
            position: {
              x: 'left',
              y: 'bottom'
           }
        });
        $("#vis-icon-box").jBox("Mouse", { ///
            theme: 'TooltipDark',
            content: 'Show timelines',
            position: {
              x: 'left',
              y: 'bottom'
           }
        });
     },
     isAllZeros (value, index, ar) {
        if (value == 0) { // 判断数组中元素是否为0.
            return true;
        }else {
            return false;
        }
     },
     egoNetTimeCurves(timeCurveObj){
      /*
        timeCurveObj: {ego1: {"2000-08": {"point": [x, y], "feature_vec": []}, "2000-09": {}}, ...}
      */
      let this_ = this;      
      d3.select("#svg-ego-time-curve").remove(); // 清除svg中旧的内容.
      
      let svg = d3.select("#time-curve-view").append("svg")
                                .attr("id", "svg-ego-time-curve")
                                .attr("width", this_.svgWidth)
                                .attr("height", this_.svgHeight);
      let defsSvg = svg.append("defs");
      defsSvg.selectAll("marker")
             .data(["end"]) // .data([{id:"end-arrow", opacity:1}, {id:"end-arrow-fade", opacity:0.1}])            
             .enter().append("marker")
              .attr("id", function(d) { return d; })
              .attr("viewBox", "0 -5 10 20")
              .attr("refX", 20)
              .attr("refY", 0)
              .attr("markerWidth", 9)
              .attr("markerHeight", 15)
              .attr("opacity", 0.6)
              .attr("orient", "auto")
            .append("path")
              .attr("fill", "#e31a1c") 
              .attr("d", "M0,-5L10,0L0,5"); 
      // // 光晕效果 start
      // let glow = defsSvg.append("filter")
      //                   .attr("id", "glow");
      // glow.append("feGaussianBlur")
      //   .attr("class", "blur")
      //   .attr("result", "coloredBlur")
      //   .attr("stdDeviation", "3");
      // let femerge = glow.append("feMerge");
      // femerge.append("feMergeNode").attr("in", "coloredBlur");
      // femerge.append("feMergeNode").attr("in", "coloredBlur");
      // femerge.append("feMergeNode").attr("in", "coloredBlur");
      // femerge.append("feMergeNode").attr("in", "SourceGraphic");
      // // 光晕效果 end     
      let g = svg.append("g")
                 .attr("class", "everything");      
      
      // fixme: 为获得最大最小xy坐标做准备.
      let slectedEgoList = this_.$store.getters.getselectedEgoList; // [x, ...]
      let egoPointList = []; // [[x, y], ...],该视图中所有节点构成的一个数组, 用于后续找到最小最大值.
      let egoPointObj = {}; // {"mao": {nodes: [{time_step: "2000-03", point: [x, y], feature_vec: [x, ...]}, ...], links: [{source: [x, y], target: [x, y]}, ...]}, ...}
      let dateStringArray = null; // [2000-03, 2000-4, 2000-05]
      if(this_.$store.getters.gettimeStepSlice.length == 0){ //整个时间轴.
        dateStringArray = this_.$store.getters.gettimeStepList;
      }
      else{ // 时间区间
        let startTime = this_.$store.getters.gettimeStepSlice[0];
        let endTime = this_.$store.getters.gettimeStepSlice[1];
        let startTimeIndex = this_.$store.getters.gettimeStepList.indexOf(startTime);
        let endTimeIndex = this_.$store.getters.gettimeStepList.indexOf(endTime);
        dateStringArray = this_.$store.getters.gettimeStepList.slice(startTimeIndex, endTimeIndex + 1);
      }
      
      // let colorMapList = chroma.scale(['#fee5c2','#7f0000']).mode('lch').colors(dateStringArray.length); // 颜色数量 == 一条time curve中节点的数量, ["#4abd8c", ...]
      // 以下几个属性用于bubbleSets.
      let outlinePoints = []; // [[{}, ...], [{}, ...], ...]
      // let outlineEdges = []; // [[{x1: x, y1: x, x2: x, y2: x}], ...]
      let widthPoint = 1; // 方块的大小.
      let heightPoint = 1;
      for(let i=0; i<slectedEgoList.length; i++){
        let selectedEgo = slectedEgoList[i];
        let selectedTimeStepObj = timeCurveObj[selectedEgo]; // {"2000-08": {"point": [x, y], "feature_vec": []}, "2000-09": {}}
        // let timeStepList = dateStringArray; // ["2000-08", "2000-09"]
        let nodesTempList = []; // [{ego: x, order: x, time_step: x, point: [x, y], feature_vec: [x, ...]}, ...]
        let linksTempList = []; // [{}, ...]
        let outlinePointsItem = []; // [{x: x, y:x, width: x, height: x}, ...]
        // let outlineEdgesItem = []; // [{x1: x, x2: x, y1: x, y2: x}, ...]
        for(let j=0; j<dateStringArray.length; j++){
           let timeStep = dateStringArray[j];                  
           egoPointList.push(selectedTimeStepObj[timeStep].point); // [[x, y], ...]
           let nodeTempObj = {};
           let linkTempObj = {};
           nodeTempObj["ego"] = selectedEgo;
           nodeTempObj["order"] = j; // 节点顺序,按照时间顺序进行排列.
           nodeTempObj["time_step"] = timeStep;
           nodeTempObj["point"] = selectedTimeStepObj[timeStep].point;
           nodeTempObj["feature_vec"] = selectedTimeStepObj[timeStep].feature_vec;
           nodesTempList.push(nodeTempObj); // [{order: 0, time_step: "2000-03", point: [x, y], feature_vec: [x, ...]}, ...]
           outlinePointsItem.push({x: selectedTimeStepObj[timeStep].point[0], y: selectedTimeStepObj[timeStep].point[1], width: widthPoint, height: heightPoint});
           if(j < (dateStringArray.length - 1)){
            linkTempObj["order"] = j;
            linkTempObj["source"] = selectedTimeStepObj[timeStep].point;
            linkTempObj["target"] = selectedTimeStepObj[dateStringArray[j + 1]].point;
            linksTempList.push(linkTempObj); // [{source: [], target: [], order: 0}, ...]
            // outlineEdgesItem.push({x1: selectedTimeStepObj[timeStep].point[0], y1: selectedTimeStepObj[timeStep].point[1], x2: selectedTimeStepObj[dateStringArray[j + 1]].point[0], y2: selectedTimeStepObj[dateStringArray[j + 1]].point[1]});
           }           
        }        
        let nodeLinksObj = {};
        nodeLinksObj["nodes"] = nodesTempList;
        nodeLinksObj["links"] = linksTempList;
        egoPointObj[selectedEgo] = nodeLinksObj; // {"mao": {nodes: [{time_step: "2000-03", point: [x, y], feature_vec: [x, ...]}, ...], links: [{source: [x, y], target: [x, y]}, ...]}, ...}
        outlinePoints.push(outlinePointsItem); // [[{}, ...], ...]
        // outlineEdges.push(outlineEdgesItem); // [[{}, ...], ...]
      }

      let min_x = d3.min(egoPointList, function(d) {        
        return d[0];
      });
      
      let max_x = d3.max(egoPointList, function(d) {        
        return d[0];
      });

      let min_y = d3.min(egoPointList, function(d) {       
        return d[1];
      });

      let max_y = d3.max(egoPointList, function(d) {        
        return d[1];
      });

      let x = d3.scaleLinear().domain([min_x, max_x]).range([this_.MARGIN, this_.svgWidth - this_.MARGIN]);
      let y = d3.scaleLinear().domain([min_y, max_y]).range([this_.svgHeight - this_.MARGIN, this_.MARGIN]);        
      
      // d3.selectAll(".color-legend-item").remove(); // 使用selectAll, 否则出错.
      let colorLegendBox = d3.select("#timecurve-legend-box"); // 颜色图例
      // 放大点集合中点坐标      
      let outlinePointsMap = []; // [[{}, ...], ...]
      for(let i=0; i<outlinePoints.length; i++){
        let item = outlinePoints[i]; // [{}, ...]
        let itemMap = item.map(function (obj, idx){ // [{}, ...]
            let temp = {};
            temp.x = x(obj.x);
            temp.y = y(obj.y);
            temp.width = obj.width;
            temp.height = obj.height;
            return temp;
        });
        outlinePointsMap.push(itemMap);
      }      
      // console.log("outlinePointsMap");console.log(outlinePointsMap); 
      // 创建一个g元素, 用于管理轮廓曲线.
      let outlineElement = g.append('g').attr("id", "outlines");
      // 根据选中的ego,逐条地绘制time curve.
      let counterNumForR = -1; // 用于统计选中的ego的数量, 实现半径渐变
      for(let i=0; i<slectedEgoList.length; i++){
         let recordEmptyTimestep = []; // [0, 2, 8, ...], 用于记录空的时间步, 以便于后续对时间曲线的节点进行区别.
         let colorItem = this_.colorChangeList[i];
         let colorMapList = chroma.scale(colorItem).mode('lch').colors(dateStringArray.length); // 颜色数量 == 一条time curve中节点的数量, ["#4abd8c", ...]
         
         // 颜色图例
         let colorDiv = colorLegendBox.append("div").attr("class", "color-legend-item"); // 行
         // colorMapList.forEach(function(item, index){ // 列
         //   colorDiv.append("span").attr("class", "grad-step-span").attr("style", "background-color:" + item);
         // });
         // colorDiv.append("span").attr("class", "domain-min").text(this_.$store.getters.gettimeStepSlice[0]);
         // colorDiv.append("span").attr("class", "domain-max").text(this_.$store.getters.gettimeStepSlice[1]);
         let svgColor = colorDiv.append("svg").attr("class", "cl-svg-box")
                               .attr("width", 165)
                               .attr("height", 18);
                               // .attr("fill", function(){
                               //   return this_.$store.getters.getcolorSchemeList[i];
                               // });
         svgColor.append("rect").attr("class", "cl-rect")
                                .attr("x", 0)
                                .attr("y", 0)
                                .attr("width", 15)
                                .attr("height", 15)
                                .attr("fill", function(){
                                  return this_.$store.getters.getcolorSchemeList[i];
                                });
         svgColor.append("text").attr("class", "lgd-text")
                                .attr("x", 18)
                                .attr("y", 12)
                                .text(function(){                                  
                                  return this_.$store.getters.getselectedEgoObj[slectedEgoList[i]].split(":")[0] + "'s states";
                                });           

         let selectedEgo = slectedEgoList[i];
         counterNumForR += 1; // 累加
         let selectedEgoPointList = egoPointObj[selectedEgo].nodes; // [{order: 0, time_step: "2000-03", point: [x, y], feature_vec: [x, ...]}, ...]
         let pointLinksList = egoPointObj[selectedEgo].links; // [{source: [x, y], target: [x, y]}, ...]
          // fixme: 重叠点检测.
          let overlayNodeList = []; // [[0, 1, 2], [], ...], 里面记录重叠点的位置索引.
          let overlayNodeSet = new Set();
          
          for(let i=0; i<selectedEgoPointList.length; i++){
             if(overlayNodeSet.has(i)){
                continue;
             }
             else{
               let nodePoint = selectedEgoPointList[i].point; // [x, y]
               let overlayNodes = [];
               overlayNodes.push(i);
               overlayNodeSet.add(i);
               for(let j=i+1; j<selectedEgoPointList.length; j++){
                let nextNodePoint = selectedEgoPointList[j].point;
                if(nodePoint[0].toFixed(5) == nextNodePoint[0].toFixed(5) && nodePoint[1].toFixed(5) == nextNodePoint[1].toFixed(5)){
                   overlayNodes.push(j);
                   overlayNodeSet.add(j);
                }
               }
               overlayNodeList.push(overlayNodes); // [[0, 1], ...]
             }
          }
          
          /************************ 放大原节点坐标, 适应当前视图. 将输入坐标根据比例进行变换 *********************************/
      
          selectedEgoPointList.forEach(function (nodeObj, index){ // [{order: 0, time_step: "2000-03", point: [x, y], feature_vec: [x, ...]}, ...]
             nodeObj.point = [x(nodeObj.point[0]), y(nodeObj.point[1])];
             // if(nodeObj.feature_vec) 
             if(nodeObj.feature_vec.every(this_.isAllZeros)){
               // recordEmptyTimestep.push({order: nodeObj.order, time_step: nodeObj.time_step}); // [{order: 0, time_step: '2000-03'}, ...]
               recordEmptyTimestep.push(nodeObj.order);
             }            
          });
          // console.log("recordEmptyTimestep");console.log(recordEmptyTimestep);
          pointLinksList.forEach(function (linkObj, index){ // [{source: [x, y], target: [x, y]}, ...]
             linkObj.source = [x(linkObj.source[0]), y(linkObj.source[1])];
             linkObj.target = [x(linkObj.target[0]), y(linkObj.target[1])];
          });
          /*********************** END ***************************************************/           
          for(let i=0; i<overlayNodeList.length; i++){ // overlayNodeList = [[0, 1, 2], [], ...], 里面记录重叠点的位置索引.
             let nodesList = overlayNodeList[i]; // nodesList = [0, 1, 2]
             if(nodesList.length > 1){ // 有重叠点.
               // 将重叠点放置在圆上, 但是实际布局出来的结果会变成椭圆, 因为
               let cX = selectedEgoPointList[nodesList[0]].point[0]; // 以重叠点的坐标为圆心cx
               let cY = selectedEgoPointList[nodesList[0]].point[1]; // 以重叠点的坐标为圆心cy
               let R = 8 + counterNumForR * 5; // 根据ego数量, 动态调节半径大小.
               
               nodesList.forEach(function(item, index){ // [0, 7, 8]
                 //重新定位.                                
                 let degreeCircleDivide = 2*Math.PI / nodesList.length; // 按照重叠节点的数量划分圆, 然后将重叠节点安置在圆上.
                 let x = cX + R*Math.sin(degreeCircleDivide * index);
                 let y = cY + R*Math.cos(degreeCircleDivide * index);
                 selectedEgoPointList[item].point = [x, y]; // 更新重叠点的坐标.
                 // fixme: 更新重叠点对应边的坐标.
                 if(item == 0){ // 如果是第一个节点
                    pointLinksList[item].source = [x, y];
                 }
                 else if(item == (selectedEgoPointList.length - 1)){ // 如果是最后一个节点
                    pointLinksList[item - 1].target = [x, y];
                 }
                 else{ // 其他点, 则需要更新两条边的终点和起点.
                  pointLinksList[item].source = [x, y];
                  pointLinksList[item - 1].target = [x, y];
                 }
                 
               });
             }
        }        
          // end 重叠点检测.
        let gegoTimeCurve = g.append('g').attr("class", "ego-time-curve");
        // fixme: 先绘制点集合的轮廓线, 然后绘制画边打点.
        let innerPointList = outlinePointsMap[counterNumForR]; // 当前ego对应的点集.
        let newArr = outlinePointsMap.filter(function(val, idx){ // [[], [], []]
            if(idx !== counterNumForR){ // 筛选出其他ego的点集.
              return true;
            }
        });          
        let outerPointList = this_.mergeArrays(...newArr);       
        let pad = 1;                 
        let dAttrPath = this_.getOutline(innerPointList, outerPointList, pad); // path的属性d的值, 也就是一个包围曲线. outlineEdges[counterNumForR]          
        this_.createPathLayer(outlineElement, this_.$store.getters.getcolorSchemeList[counterNumForR], dAttrPath);
        // fixme: 先画边, 然后再打点, 这样在点的位置上, 边就被点覆盖了.     
        let enter_lines = gegoTimeCurve.append('g').attr("class", "time-steps-lines") // 节点之间的线段.
                     .selectAll('.time-line')
                     .data(pointLinksList) // [{source: [x, y], target: [x, y]}, ...]
                     .enter()
                     .append('line')
                     .attr('class', function(d, index){                      
                      let egoId = selectedEgo;
                      return 'time-line ' + "line-" + egoId.replace(/\./g, "-") + " line-" + egoId.replace(/\./g, "-") + "-" + index + "-" + (index + 1);
                     })
                     .attr("stroke", function(d){                      
                      return this_.$store.getters.getcolorSchemeList[counterNumForR];
                     })                     
                     .style('stroke-opacity', 1)
                     .style('display', function(){
                        if(this_.isVisLine){                        
                          return "block";
                        }else{
                          return "none";
                        }
                     })
                     // .style("filter", "url('#glow')") // style="stroke-width: 1; stroke: rgb(232, 17, 15); filter: url("#glow");"
                     .attr("stroke-width", function(d) { return 1; });

        // 坐标已经被放大了.
        enter_lines.attr("x1", function (d) { return d.source[0]; })
                        .attr("y1", function (d) {return d.source[1];})
                        .attr("x2", function (d) {
                          return d.target[0];                            
                        })
                        .attr("y2", function (d) {
                          return d.target[1];                            
                        }); 

        
        let timeStepPointG = gegoTimeCurve.append('g').attr("class", "time-steps-points"); // fixme: 中期时加的
        let enter_points = timeStepPointG // fixme: 中期时加的
                     .selectAll('.point')
                     .data(selectedEgoPointList)
                     .enter()
                     .append('g')
                     .attr('class', function(d){
                        // let className = null;
                        let egoId = selectedEgo;
                        return "point " + "point-" + egoId.replace(/\./g, "-"); // 效果: mao.tingyun.cher ===> mao-tingyun-cher
                         
                     })
                     .attr('transform', function(d) {
                        return "translate(" + (d.point[0]) + "," + (d.point[1]) + ")"; // 坐标已经被放大了.
                     });                     
      
        let circlePoints = enter_points.append('circle').attr("r", this_.stateNodeR)
                                     .attr("class", function(d){
                                        let egoId = selectedEgo;
                                        return "node-" + egoId.replace(/\./g, "-") + " node-" + egoId.replace(/\./g, "-") + "-" + d.order; // 效果: mao.tingyun.cher ===> mao-tingyun-cher 
                                     })
                                     .attr("fill", function(d){                                       
                                       if(recordEmptyTimestep.indexOf(d.order) == -1){ // 不在里面                                          
                                          return this_.$store.getters.getcolorSchemeList[counterNumForR];
                                       }
                                       else{
                                          return "white";
                                       }                                      
                                       
                                     })
                                     .attr("stroke", function(d){
                                        let endOrder = dateStringArray.length - 1; // end point                                        
                                        return this_.$store.getters.getcolorSchemeList[counterNumForR];
                                     })
                                     .attr("stroke-width", function(d){
                                      let endOrder = dateStringArray.length - 1; // end point
                                        if(d.order == 0){ // start point
                                            return "2"
                                        }
                                        else if(d.order == endOrder){ // end point
                                          return "2";
                                        }
                                        else{
                                          return "2";
                                        }
                                     })                                     
                                     .on("mouseover", function (e){                                          
                                        if(!this_.isVisLine){
                                            d3.selectAll("#svg-ego-time-curve " + "line").style('display', "block");
                                        }
                                        if(e.order > 0){                                              
                                         d3.select("#svg-ego-time-curve " + ".line-" + selectedEgo.replace(/\./g, "-") + "-" + (e.order - 1) + "-" + e.order).attr('marker-end', 'url(#end)');                                              
                                         }
                                         if(e.order < selectedEgoPointList.length - 1){
                                           d3.select("#svg-ego-time-curve " + ".line-" + selectedEgo.replace(/\./g, "-") + "-" + e.order + "-" + (e.order + 1)).attr('marker-end', 'url(#end)'); // line-susan-scott-14-15
                                         }                                               
                                         d3.selectAll("#svg-ego-time-curve " + "circle").style('opacity', 0.15);
                                         if(e.order == 0){
                                           d3.selectAll("#svg-ego-time-curve " + "circle.marker_start").style('opacity', 1);
                                         }
                                         if(!this_.isVisLine){
                                            d3.selectAll("#svg-ego-time-curve " + "line").style('opacity', 0);
                                         }else{
                                            d3.selectAll("#svg-ego-time-curve " + "line").style('opacity', 0.15);
                                         }
                                         d3.selectAll("#svg-ego-time-curve " + "path.marker_end").style('opacity', e.order == selectedEgoPointList.length - 1 ? 1 : 0.15);
                                         d3.selectAll("#svg-ego-time-curve " + ".node-" + selectedEgo.replace(/\./g, "-") + "-" + e.order).style('opacity', 1);                                               
                                         if(e.order < selectedEgoPointList.length - 1){
                                            d3.selectAll("#svg-ego-time-curve " + ".node-" + selectedEgo.replace(/\./g, "-") + "-" + (e.order + 1)).style('opacity', 1);
                                            d3.selectAll("#svg-ego-time-curve " + ".line-" + selectedEgo.replace(/\./g, "-") + "-" + e.order + "-" + (e.order + 1)).style('opacity', 1);
                                         }                                        
                                        
                                         if(e.order > 0){
                                            d3.selectAll("#svg-ego-time-curve " + ".line-" + selectedEgo.replace(/\./g, "-") + "-" + (e.order - 1) + "-" + e.order).style('opacity', 1);
                                            d3.selectAll("#svg-ego-time-curve " + ".node-" + selectedEgo.replace(/\./g, "-") + "-" + (e.order - 1)).style('opacity', 1);
                                         }
                                     })
                                     .on("mouseout", function (e){                                          
                                         if(!this_.isVisLine){
                                            d3.selectAll("#svg-ego-time-curve " + "line").style('display', "none");
                                         } 
                                         if(e.order > 0){
                                            d3.select("#svg-ego-time-curve " + ".line-" + selectedEgo.replace(/\./g, "-") + "-" + (e.order - 1) + "-" + e.order).attr('marker-end',''); 
                                         }
                                         if(e.order < selectedEgoPointList.length - 1){
                                           d3.select("#svg-ego-time-curve " + ".line-" + selectedEgo.replace(/\./g, "-") + "-" + e.order + "-" + (e.order + 1)).attr('marker-end',''); // line-susan-scott-14-15
                                         }                                        
                                         d3.selectAll("#svg-ego-time-curve " + "circle").style('opacity', 1);
                                         d3.selectAll("#svg-ego-time-curve " + "line").style('opacity', 1);  
                                         d3.selectAll("#svg-ego-time-curve " + "path.marker_end").style('opacity', 1);
                                     });
        circlePoints.on("click", function(event){
          // {ego: "frank.ermis", order: 1, time_step: "2000-04", point: Array(2), feature_vec: Array(6)}
          let selectedEgo = event.ego; // e.g., "frank.ermis"
          let timeStep = event.time_step; // 2000-04
          // node-frank-ermis-1
          d3.selectAll("#svg-ego-time-curve " + ".node-" + selectedEgo.replace(/\./g, "-") + "-" + event.order).attr("stroke", "black").attr("stroke-width", 2); // 高亮点. 
          // timeStep
          let sliceStartIdx = 0; // 时间区间的起始位置.
          let sliceEndIdx = this_.$store.getters.gettimeStepList.length - 1;
          if(this_.$store.getters.gettimeStepSlice.length > 0){
            sliceStartIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);
            sliceEndIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[1]);
          }
          let timeStepIndex = this_.$store.getters.gettimeStepList.indexOf(timeStep);
          let moveX = 8 + (timeStepIndex - sliceStartIdx) * this_.$store.getters.gettimeStepEgonetW;
          $("#dyegonet-time-line").scrollLeft(moveX);
          $("#egonets-time-step-box").scrollLeft(moveX);                 
          $("#show-egonet-seq").scrollLeft(moveX); // div同步横向滚动条
          // console.log("circlePoints.on jjjjjjj");
        });
        enter_points.append('title').text(function(d, i) {
          // console.log("enter_points d d d d"); console.log(d);
          if(this_.$store.getters.getselectedDataset == "enron"){
            return selectedEgo + ": " + d.time_step;
          }
          if(this_.$store.getters.getselectedDataset == "tvcg"){
            return d.time_step;
          }        
        });
        enter_points.filter(function (d){
                      return d.order == 0; // the first dot.
                   })
                   .append("circle")
                      .attr("cx", 0)
                      .attr("cy", function(d){
                         return -(this_.stateNodeR + 4);
                      })
                      .attr('r', 3) // 标记点的半径
                      .attr("class", "marker_start")
                      .attr('fill', function (d) {
                          return this_.$store.getters.getcolorSchemeList[counterNumForR];
                      });        
        enter_points.filter(function (d){
                        return d.order == (selectedEgoPointList.length - 1); // the last dot.
                     })
                     .append("path")
                     .attr("class", "marker_end")
                     .attr("d", function(d){                                      
                        let triAgX = 3;
                        let triBY = this_.stateNodeR + 2;
                        let triAgY = triBY + 5;
                        let pathStr = "M -" + triAgX.toString() + " -" + triAgY.toString() + " L " + triAgX.toString() + " -" + triAgY.toString() + " L 0 -" + triBY.toString() + " z";
                        return pathStr;
                      })                                                                      
                     .attr('fill', function (d) {
                          return this_.$store.getters.getcolorSchemeList[counterNumForR];
                      })
                     .attr("stroke", function (d) { // stroke='color'; stroke-width='4'
                          return this_.$store.getters.getcolorSchemeList[counterNumForR];
                      });

      }
      
      
      let zoomHandler = d3.zoom()
                          .scaleExtent([0.5, 25]) // zoom range
                          .on("zoom", updateOverview);
      zoomHandler(svg);
      function updateOverview(){
        // 更新x,y之后再缩放  newX, newY     
        let x = d3.scaleLinear().domain([this_.MARGIN, this_.svgWidth - this_.MARGIN]).range([this_.MARGIN, this_.svgWidth - this_.MARGIN]);
        let y = d3.scaleLinear().domain([this_.svgHeight - this_.MARGIN, this_.MARGIN]).range([this_.svgHeight - this_.MARGIN, this_.MARGIN]);
        let newX = d3.event.transform.rescaleX(x);
        let newY = d3.event.transform.rescaleY(y);  
        d3.selectAll("#outlines > *").remove(); // 删除所有的path元素.      
        let outlinePointsMap = []; // [[{}, ...], ...]
        for(let i=0; i < slectedEgoList.length; i++){
          outlinePointsMap.push([]);
        }
        g.selectAll('.point')                        
         .attr('transform', function(d) {
          let idx = slectedEgoList.indexOf(d.ego);
          outlinePointsMap[idx].push({x: newX(d.point[0]), y: newY(d.point[1]), width: widthPoint, height: heightPoint});
          return "translate(" + (newX(d.point[0])) + "," + (newY(d.point[1])) + ")";
        });
        g.selectAll(".time-line").attr("x1", function (d) { return newX(d.source[0]); })
                        .attr("y1", function (d) { return newY(d.source[1]); })
                        .attr("x2", function (d) {
                          return newX(d.target[0]);                            
                        })
                        .attr("y2", function (d) {
                          return newY(d.target[1]);                            
                        });
        let debounceFunc = this_.debounce(function(){
          d3.selectAll("#outlines > *").remove(); // 删除所有的path元素.
          // fixme: 对轮廓进行缩放.
          for(let i=0; i<outlinePointsMap.length; i++){
            let innerPointList = outlinePointsMap[i]; // 当前ego对应的点集.
            let newArr = outlinePointsMap.filter(function(val, idx){ // [[], [], []]
                if(idx !== i){ // 筛选出其他ego的点集.
                  return true;
                }
            });          
            let outerPointList = this_.mergeArrays(...newArr);       
            let pad = 1;                 
            let dAttrPath = this_.getOutline(innerPointList, outerPointList, pad); // path的属性d的值, 也就是一个包围曲线. outlineEdges[counterNumForR]          
            this_.createPathLayer(outlineElement, this_.$store.getters.getcolorSchemeList[i], dAttrPath);
          }
        }, 500); 
        debounceFunc();               

      }                   
      svg.on("dblclick.zoom", null); // fixme:失能双击放大.
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
     }     
    },
    created(){
      console.log("created");      
    },
    mounted(){
      console.log("mounted");
      let this_ = this; 
      this_.jBoxInstance.legendJbox = new jBox('Modal', {
                  id: "jBoxLegend-state",
                  addClass: "jBoxLegendInfo",  // 添加类型,这个功能很棒啊!
                  attach: '#legend-icon-img',  // 这是历史走廊的图标.点击这个图标打开历史走廊弹窗.
                  maxWidth: 180,
                  // height: 200,
                  maxHeight: 450,
                  adjustTracker:true,
                  title: 'Color Legend',
                  overlay: false,
                  zIndex: 1005, // fixme:注意多个jBox实例之间zIndex的值决定与最后一个实例.
                  createOnInit: true,
                  content: $("#timecurve-legend-box"),  // jQuery('#jBox-content') 
                  draggable: true,
                  repositionOnOpen: false,
                  repositionOnContent: true,                  
                  // position:{x: 300, y: 350}
                  target: $('#tool-for-timecurve'),
                  offset: {x: 162, y: 0}
         });
      this_.jBoxInstance.egosnpDetail = new jBox("Modal", {
            id: "jBox-egonetstinfo",
            addClass: "jBox-egonetstinfo",  // 添加类型,这个功能很棒啊!
            attach: '.egonetstOVContextMenu',  // 这是历史走廊的图标.点击这个图标打开历史走廊弹窗.
            maxWidth: 200,            
            maxHeight: 550,
            // adjustTracker:true,
            title: 'State Details',
            overlay: false,
            zIndex: 1005, // fixme:注意多个jBox实例之间zIndex的值决定与最后一个实例.
            createOnInit: true,
            content: $("#overview-egonetst-info"),  // jQuery('#jBox-content') 
            draggable: true,
            repositionOnOpen: false,
            repositionOnContent: true,    
            target: $('#time-curve-view'),
            offset: {x: -110, y: -60},            
            onCloseComplete: function(){               
               let pointSt = '#timecurveview .ego-time-curve .time-steps-points .point' + " .node-" + this_.curViewEgo.replace(/\./g, "-") + "-" + this_.order;
               d3.select(pointSt).attr("stroke", "#d1d1d1").attr("stroke-width", 1); // 高亮点. 
               this_.curViewEgo = null;
               this_.curTimeStep = null; 
               this_.order = null;      
            }
      });
      d3.select("#tool-for-timecurve #vis-icon-img").on("click", function(){         
         if(this_.isVisLine){ // true
            this.setAttribute("src", "../../static/img/novis.svg");
            // this.setAttribute("src", "../../static/img/vis.svg");
            this_.isVisLine = false;
            d3.selectAll("#svg-ego-time-curve " + "line").style('display', "none");
         }else{ // false
            this.setAttribute("src", "../../static/img/vis.svg");
            // this.setAttribute("src", "../../static/img/novis.svg");
            this_.isVisLine = true;
            d3.selectAll("#svg-ego-time-curve " + "line").style('display', "block");
         }
      });
      this_.tooltipForOverview();
      this_.contextMenuForSnp();
    },
    updated(){
      console.log("timeCurveView updated");
    },
    beforeDestroy(){
      console.log("timeCurveView beforeDestroy");
    }   
  }
</script>

<style>
  @import "../../static/css/jBox.css";
  @import "../../static/css/jquery.contextMenu.css";
  .jBox-Modal.jBox-closeButton-title .jBox-title{
    padding-top: 2px;
    padding-bottom: 2px;
    padding-left: 2px;
  }
</style>