<template>
  <div id="egonet-sequences-box">    
    <div id="dyegonet-view">
      <div id="tool-for-egonetseq">          
          <div class="egonetseq-level-box">
            <img class="egonetseq-img-icon" id="egonetseq-level-icon" width="17" height="17" src="../../static/img/level.svg">
          </div>
          <div class="egonetseq-legend-box">
            <img class="egonetseq-img-icon" id="egonetseq-legend-icon" width="15" height="15" src="../../static/img/stackG.png">
          </div>
          <div class="egonetseq-layout-box">
            <img class="egonetseq-img-icon" id="egonetseq-layout-icon" width="15" height="15" src="../../static/img/layout.svg">
          </div>          
      </div>
      <div id="overviews-each-timestep">
        <egooverviewtimestep :svgWidth="selectedTimestepNum * $store.getters.gettimeStepEgonetW + margin.left + margin.right" :timestepNum="selectedTimestepNum"></egooverviewtimestep>
      </div>         
      <div id="dyegonet-time-line" @scroll="scrollOperate">      
       <svg id="svg-time-line" :width="selectedTimestepNum * $store.getters.gettimeStepEgonetW + margin.left + margin.right" :height="timeLineH"></svg>
      </div>       
      <div id="show-egonet-seq"> 
       <svg id="svg-dyegonet" :width="selectedTimestepNum * $store.getters.gettimeStepEgonetW + margin.left + margin.right" :height="$store.getters.getselectedEgoList.length * ($store.getters.gettimeStepEgonetH + marginDyEgonet) + margin.bottom"></svg>
      </div> 
    </div>
    <div id="overview-egonetnodes-info"></div>          
  </div>  
</template>

<script>
  import * as d3 from '../../static/js/d3.v4.min.js'
  // import {d3Fisheye} from '../../static/js/fisheye.js'
  import {vueFlaskRouterConfig} from '../flaskRouter'
  import bus from '../eventbus.js' // 事件总线.  
  import axios from 'axios'
  import {mapGetters} from "vuex"
  import {jBox} from "../../static/js/jBox.js"
  import {d3GraphLayout} from "../../static/js/forceDyEgonet.js"
  import $ from 'jquery'
  import * as $$ from "../../static/js/jquery.min.js"
  import "../../static/js/jquery.contextMenu.js"
  import "../../static/js/jquery.ui.position.js" 
  import egooverviewtimestep from "@/components/egoOverviewTimeStep"
    
  export default {
    data() {
      return {
        svgWidth: 1280,
        svgHeight: 0,
        // dyegonetHeight: 120, // 选中的dyegonet(egonet序列)所占的高度 
        timeLineH: 24, // 时间轴的高度
        marginDyEgonet: 15, // 动态ego网路的间隔.
        nodeNameText: 12, // 用于放置节点的名字.   
        gEgonet: null,        
        margin: {left: 10, top: 10, right: 10, bottom: 10},
        selectedTimestepNum: 0, // 被选中的时间步的数量.
        // timeStepEgonetH: 150, // 每个时间步下egonet所占高度.
        // timeStepEgonetW: 150, // 每个时间步下egonet所占宽度.         
        // altersColor: "#a7a7a7", // alters的颜色.
         // fixme: 中期时加的
        egonetLevel1: true, // 默认只显示一层, false时, 切换到2层.  
        layoutMargin: 4, // 格子中布局的margin大小, 这样避免节点直接布局在左上角. 
        layoutMethod: "noname", 
        layoutMethodFlag: false,
        clickActorSet: {}, // {ego: [x, x, ...], ...}
        jBoxInstance: { // jBoxInstance.nodeDetail
          nodeDetail: null
        },
        curViewNode: null,
        curClickedEgo: null,
        curTimeStep: null,
        // markRectTextList: [] // [[rect, text], ...]     
      }
    },
    components:{
      egooverviewtimestep
    },    
    computed: {      
      ...mapGetters([
         // "getselectedEgoList",
         "gettimeStepList",
         "gettimeStepSlice"
        ])     
    },
    watch: {           
      gettimeStepList: function(curVal, oldVal){
        let this_ = this;
        if(curVal.length > 0){
          this_.updateTimestepNum();
        }        
      },
      gettimeStepSlice: function(curVal, oldVal){
        let this_ = this;
        if(curVal.length > 0){
          this_.updateTimestepNum();
        }
      }     
    },
    methods: {
      diagonal(d) { // 
        let path = "M" + d.source[0] + "," + d.source[1]
          + "C" + d.source[0] +  "," + (d.source[1] + d.target[1]) / 2
          + " " + d.target[0] + "," + (d.source[1] + d.target[1]) / 2
          + " " + d.target[0] + "," + d.target[1];
        //return "M" + d.source.y + "," + d.source.x
        //      + "C" + (d.source.y + d.target.y) / 2 + "," + d.source.x
        //      + " " + (d.source.y + d.target.y) / 2 + "," + d.target.x
        //      + " " + d.target.y + "," + d.target.x;
        return path;
      },
       getStatDiagramForDetail(dbname, selector, egoInfoObj, barWidth, barHeight, svgHeight, curTimeStep, nodeId, tslice){
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
        // let customizeName = ['degree', 'density', 'avg_weight', 'num_edges_alters', 'num_2_alters', 'avg_alters_alters'];
        let curTimeStepIdx = this_.$store.getters.gettimeStepList.indexOf(curTimeStep)
        let barMargin = 2;
        let sliceStartIdx = tslice[0]; // 时间区间的起始位置.
        let sliceEndIdx = tslice[1]; 
        curTimeStepIdx = curTimeStepIdx - sliceStartIdx;
        
        let newftValList = [];
        for(let i=sliceStartIdx; i<=sliceEndIdx; i++){
          let val = egoInfoObj.tsliceW[i.toString()];
          newftValList.push(val);
        }
        let maxVal = Math.max(...newftValList);       
        let detaH = 0;
        if(maxVal > 0){
          detaH = barHeight / maxVal;
        }
        let divBox = ftDiv.append("div").attr("class", "ft-div");
        divBox.append("div").attr("class", "dt-ft-tag tooltip").text("Ego-Alter Weights:").append('span').attr("class", "tooltiptext").text(function(){
          return "Wieght Evolution";
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
        egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
          return "Timestep: " + curTimeStep;
        });
        egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
          return "Name: " + egoInfoObj.nattr.name;
        });
        if(dbname == "enron"){
          egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
            return "Position: " + egoInfoObj.nattr.position;
          }); 
        }
        egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
          return "Lifespan: " + this_.$store.getters.gettimeStepList[egoInfoObj.lifespan[0]] + " - " + this_.$store.getters.gettimeStepList[egoInfoObj.lifespan[1]];
        });
        egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
          return "Occur_Freq: " + egoInfoObj.occurfreq;
        });   
        if(dbname == "tvcg"){
          // total_p_num
          // p_num_year
          // r_interests
          // org        
          egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
            return "Affiliation: " + egoInfoObj.nattr.org.split(";")[0];
          });
          egoInfo.append("div").attr("class", "ego-if-div").append("span").attr("class", "ego-if-sp").text(function(){
            let splitArr = egoInfoObj.nattr.r_interests.split(";"); // [x, x, ...]
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
            return "Total_Pub_Num: " + egoInfoObj.nattr.total_p_num;
          });                   
          let ftValList = egoInfoObj.nattr.p_num_year;
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
      getDyEgonetNodeInfo(egoId, nodeId, curTimeStep){ // 获得右键节点的信息.
        let this_ = this;
        let dbname = this_.$store.getters.getselectedDataset;
        let selector = "#overview-egonetnodes-info"; 
        let barWidth = 4;
        let barHeight = 12;
        let svgHeight = 13; 
        let sliceStartIdx = 0; // 时间区间的起始位置.
        let sliceEndIdx = this_.$store.getters.gettimeStepList.length - 1;
        if(this_.$store.getters.gettimeStepSlice.length > 0){
          sliceStartIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);
          sliceEndIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[1]);
        }
        let tslice = [sliceStartIdx, sliceEndIdx];      
        let param = {dbname: dbname, egoId: egoId, nodeId: nodeId, tslice: tslice};
          axios.post(vueFlaskRouterConfig.nodeDetail, {
            param: JSON.stringify(param)
        })
        .then((res) => {
            let egoInfoObj = res.data; 
            // console.log("getDyEgonetNodeInfo egoInfoObj"); console.log(egoInfoObj);        
            this_.getStatDiagramForDetail(dbname, selector, egoInfoObj, barWidth, barHeight, svgHeight, curTimeStep, nodeId, tslice);
          })
        .catch((error) => {            
          console.error(error);
        });
      },
      contextMenuForNode(){ // 节点右键设计.
        let this_ = this;
        $.contextMenu({ 
          // fixme: contextMenu插件是一个事件类型的,也就是说,mounted阶段并没有'each-dyegonet-bg'这个元素,需要点击ego后才能渲染出来,但是由于这是一个事件,则直接在mounted里面注册,一旦出现这样的元素则会直接绑定到上面,在这些元素上右键点击触发对应事件.
          selector: '#show-egonet-seq #all-dyegonets .each-dyegonet .egonet-at-timestep .nodes .node', // 绑定的元素,当在该元素右键时,就会弹出右键选择项目. 验证去掉背景矩形.
          // selector: '.each-dyegonet', // 绑定的元素,当在该元素右键时,就会弹出右键选择项目.
          className: "egonetnOVContextMenu",
          callback: function(key, options) {               
             if(key == "delete"){  // 如果点击的是"delete"选项. 
               // console.log("contexMenuEvents options.$trigger[0].__data__"); console.log(options);
               this_.jBoxInstance.nodeDetail.open();
               let nodeId = options.$trigger[0].__data__.id; // 该dyegonet的ego的ID. {id: "mike.mcconnell", name: "mike.mcconnell", position: "President"}
               let curTimeStep = null;
               let egoId = null;
               if(this_.layoutMethod == "noname"){
                curTimeStep = options.$trigger[0].parentElement.parentElement.parentElement.attributes[1].nodeValue;
                egoId = options.$trigger[0].parentElement.parentElement.parentElement.parentElement.attributes[2].nodeValue;
               }
               if(this_.layoutMethod == "SmallMultiple"){ // 由于DOM结构不同.                
                curTimeStep = options.$trigger[0].parentElement.parentElement.attributes[1].nodeValue;
                egoId = options.$trigger[0].parentElement.parentElement.parentElement.attributes[2].nodeValue;
               }
               // let order = options.$trigger[0].__data__.order;
               // this_.jBoxInstance.egosnpDetail.open(); 
               // console.log("curTimeStep egoId nodeId"); console.log(curTimeStep, egoId, nodeId);              
               this_.getDyEgonetNodeInfo(egoId, nodeId, curTimeStep);
               let pointSt = null;
               if(this_.curViewNode){
                 let pointSt = "#svg-dyegonet #all-dyegonets .each-dyegonet[name='" + this_.curClickedEgo + "']" + " .egonet-at-timestep[name='" + this_.curTimeStep + "']" + " .nodes .dyegovis-" + this_.curViewNode.replace(/\./g, "-"); // curTimeStep
                 // console.log("this_.clickActorSet kkkkk"); console.log(this_.clickActorSet);
                 if(this_.clickActorSet.hasOwnProperty(this_.curClickedEgo)){
                  if(this_.clickActorSet[this_.curClickedEgo].indexOf(this_.curViewNode) != -1){
                    d3.select(pointSt).attr("stroke", "#de2d26").attr("stroke-width", 1);                    
                  }else{
                    d3.select(pointSt).attr("stroke", "#d1d1d1").attr("stroke-width", 1);                    
                  }
                 }else{
                  d3.select(pointSt).attr("stroke", "#d1d1d1").attr("stroke-width", 1);
                 }                 
               }               
               pointSt = "#svg-dyegonet #all-dyegonets .each-dyegonet[name='" + egoId + "']" + " .egonet-at-timestep[name='" + curTimeStep + "']" + " .nodes .dyegovis-" + nodeId.replace(/\./g, "-"); // curTimeStep
               d3.select(pointSt).attr("stroke", "black").attr("stroke-width", 2); // 高亮点.
               this_.curViewNode = nodeId;
               this_.curTimeStep = curTimeStep;
               this_.curClickedEgo = egoId;               
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
       computeBasedWHForTimeSlice(posNumAlter1, posNumAlter2, svgWidth, svgHeight){ // 为选中的egonet序列计算每个方格中的步进宽和高.
          let this_ = this;
          let DPforWH = {}; // {sliceStartIdx: [W, H], ..., sliceEndIdx: [W, H]}
          let sliceStartIdx = 0; // 时间区间的起始位置.
          let sliceEndIdx = this_.$store.getters.gettimeStepList.length - 1;
          if(this_.$store.getters.gettimeStepSlice.length > 0){
            sliceStartIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);
            sliceEndIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[1]);
          }        
          for(let indexStep=sliceStartIdx; indexStep <= sliceEndIdx; indexStep++){
            // DPforWH[i] = null;
            let alters1Size = posNumAlter1[indexStep - sliceStartIdx];
            if(alters1Size != 0){
              let baseDetaH = 10; // 基本的步进高度.
              let baseDetaW = 10; // 基本的步进宽度.
              let detanbrs1H = 0;
              let detanbrs1W = 0;
              let adaptiveH = alters1Size * baseDetaH;
              let adaptiveW = alters1Size * baseDetaW;
              if(adaptiveH > (svgHeight - 2 * this_.layoutMargin)){
                adaptiveH = svgHeight - 2 * this_.layoutMargin;            
              }
              if(adaptiveW > (svgWidth - 2 * this_.layoutMargin)){
                adaptiveW = svgWidth - 2 * this_.layoutMargin;            
              }
              detanbrs1H = adaptiveH / alters1Size; // 如果节点数量过多, 导致adaptiveH超出方格的高度时, 节点的间距就会被压缩, 否则就按照设定的基本步进进行布局.
              detanbrs1W = adaptiveW / alters1Size;            
              DPforWH[indexStep] = [detanbrs1W, detanbrs1H];
            }else{
              // console.log("computebaseWHForGrid cherchercher");
              DPforWH[indexStep] = [0, 0];
            }
          }
          return DPforWH;
       },       
       compareLineDraw(){ // 用于连接相同时间步下的相同alters.
        // #svg-dyegonet #all-dyegonets .each-dyegonet .egonet-at-timestep[name='2000-03'] .dyegovis-fletcher-sturm
        // #svg-dyegonet #all-dyegonets .each-dyegonet[name='id']
        let this_ = this;
        let linksComp = []; // 收集当前每个时间步下所有相同节点的对比线.
        for(let egoRow = 0; egoRow < this_.$store.getters.getselectedEgoList.length - 1; egoRow++){
            // console.log("toogle compareLineDraw");
            let curEgoId = this_.$store.getters.getselectedEgoList[egoRow]; // 当前行对应的焦点Id.
            let nextEgoId = this_.$store.getters.getselectedEgoList[egoRow + 1]; // 下一行对应的焦点Id.            
            // let linksComp = []; // 存放对比线.
            this_.$store.getters.getdateStringArray.forEach(function(curdate, dateIndex){
                let curList = []; // [x, x, x, ...]
                let nextList = []; // [x, x, x, ...]
                let curPos = {}; // {id1: [x, y], id2: [x, y], ...}
                let nextPos = {}; // {id1: [x, y], id2: [x, y], ...}
                let curNodeSet = d3.selectAll("#svg-dyegonet #all-dyegonets .each-dyegonet[name='" + curEgoId + "'" + "]" + " .egonet-at-timestep" + "[name='" + curdate + "'] .nbrs1-alters .node");                
                curNodeSet.each(function(fd, index){ // {id:x, name:x, ...}
                  // console.log("curNodeSet each: " + curdate); console.log(fd);
                  // console.log("transform"); console.log(d3.select(this).attr("transform"));
                  let nodePos = d3.select(this).attr("transform").split(","); // translate(71.57142857142857,71.57142857142857)
                  let nodeX = parseFloat(nodePos[0].split("translate(")[1]);
                  let nodeY = parseFloat(nodePos[1].split(")")[0]);
                  curPos[fd.id] = [nodeX, nodeY];
                  curList.push(fd.id);
                  // console.log("translate"); console.log(d3.select(this).attr("transform")); console.log([nodeX, nodeY]);
                });
                let nextNodeSet = d3.selectAll("#svg-dyegonet #all-dyegonets .each-dyegonet[name='" + nextEgoId + "'" + "]" + " .egonet-at-timestep" + "[name='" + curdate + "'] .nbrs1-alters .node");
                nextNodeSet.each(function(fd, index){                  
                  let nodePos = d3.select(this).attr("transform").split(","); // translate(71.57142857142857,71.57142857142857)
                  let nodeX = parseFloat(nodePos[0].split("translate(")[1]);
                  let nodeY = parseFloat(nodePos[1].split(")")[0]);
                  nextPos[fd.id] = [nodeX, nodeY];
                  nextList.push(fd.id);                  
                });                
                let interSet = [curList, nextList].reduce((a, c) => a.filter(i => c.includes(i))); // 求两个列表的交集.
                // console.log("curdate"); console.log(curdate);
                // console.log("curNodeSet");console.log(curNodeSet);console.log("nextNodeSet");console.log(nextNodeSet);
                // console.log("interSet");console.log(interSet);
                // console.log("curPos");console.log(curPos);
                // console.log("nextPos");console.log(nextPos);
                
                for(let i=0; i<interSet.length; i++){ // 构造用于对比的边,中间有个锚点, 避免视觉混乱, 起到边捆绑的染作用.
                  let compNode = interSet[i];
                  let curX = dateIndex * this_.$store.getters.gettimeStepEgonetW + curPos[compNode][0];
                  let curY = egoRow * (this_.$store.getters.gettimeStepEgonetH + this_.marginDyEgonet) + curPos[compNode][1];
                  let anchorX = dateIndex * this_.$store.getters.gettimeStepEgonetW + this_.$store.getters.gettimeStepEgonetW / 2;
                  let anchorY = egoRow * (this_.$store.getters.gettimeStepEgonetH + this_.marginDyEgonet) + this_.$store.getters.gettimeStepEgonetH + this_.marginDyEgonet / 2;
                  let nextX = dateIndex * this_.$store.getters.gettimeStepEgonetW + nextPos[compNode][0];
                  let nextY = (egoRow + 1) * (this_.$store.getters.gettimeStepEgonetH + this_.marginDyEgonet) + nextPos[compNode][1];                  
                  linksComp.push({curdate: curdate, actorId: compNode, source: [curX, curY], target: [anchorX, anchorY]});
                  linksComp.push({curdate: curdate, actorId: compNode, source: [nextX, nextY], target: [anchorX, anchorY]});
                }                              
            });            
        }
        // console.log("linksComp");console.log(linksComp);
        d3.selectAll("#svg-dyegonet #gcompLines > *").remove(); // 先清除, 然后再绘制边.
        // let compLinks = d3.select("#svg-dyegonet #gcompLines").selectAll("line")
        //                    .data(linksComp) // [{source: [x, y], target: [x, y], actorId: x}, ...]
        //                    .enter().append("line")
        //                    .attr("class", function(d){
        //                       return "act-comp-path " + "compl-" + d.actorId.replace(/\./g, "-");
        //                    })
        //                    .attr("name", function(d){
        //                       return d.curdate;
        //                    })
        //                    .attr("x1", function(d){return d.source[0];})
        //                    .attr("y1", function(d){return d.source[1];})
        //                    .attr("x2", function(d){return d.target[0]})
        //                    .attr("y2", function(d){return d.target[1]})                                   
        //                    .attr("stroke", "#abaaaa") // #abaaaa, d3d3d3                                       
        //                    .attr("stroke-width", 1);
        // 使用diagonal,创建path.
        let compLinks = d3.select("#svg-dyegonet #gcompLines").selectAll("path")
                           .data(linksComp) // [{source: [x, y], target: [x, y], actorId: x}, ...]
                           .enter().append("path")
                           .attr("class", function(d){
                              return "act-comp-path " + "compl-" + d.actorId.replace(/\./g, "-");
                           })
                           .attr("name", function(d){
                              return d.curdate;
                           })
                           .attr("d", function(e){
                                return this_.diagonal(e);
                           })
                           .attr("fill", "none")
                           .attr("stroke", "#abaaaa")
                           .attr("stroke-width", 1);                          

       },
       computedetanbrs1H(alters1Size, svgWidth, svgHeight){ // 计算出两个邻居间的高和宽的步进.
          let this_ = this;
          let isBeyond = false; // 判断是否超过方格的高度和宽度. false: 没有超过, true: 超过
          let baseDetaH = 10; // 基本的步进高度.
          let baseDetaW = 10; // 基本的步进宽度.
          if(alters1Size != 0){
            let detanbrs1H = 0;
            let detanbrs1W = 0;
            let adaptiveH = alters1Size * baseDetaH;
            let adaptiveW = alters1Size * baseDetaW;
            if(adaptiveH > (svgHeight - 2 * this_.layoutMargin)){
              adaptiveH = svgHeight - 2 * this_.layoutMargin;
              isBeyond = true;
            }
            if(adaptiveW > (svgWidth - 2 * this_.layoutMargin)){
              adaptiveW = svgWidth - 2 * this_.layoutMargin;
              isBeyond = true;
            }
            detanbrs1H = adaptiveH / alters1Size; // 如果节点数量过多, 导致adaptiveH超出方格的高度时, 节点的间距就会被压缩, 否则就按照设定的基本步进进行布局.
            detanbrs1W = adaptiveW / alters1Size;            
            return [detanbrs1W, detanbrs1H, isBeyond];
          }
       },
       computenbrs1TrackLinks(nbrs1t, svgWidth, svgHeight, detanbrs1W, detanbrs1H, egots, ego, isBeyond=false, DPforWH=null, nbrs12t=null, nbrs12List=null){ // 计算追踪线的每个分段起点终点的距离.
          /*
            nbrs1t: {pos: {a1: [-1, -2, -1], ...}, tslice: {a1: [4, 6], ...}}
            detanbrs1W: 步进宽度.
            detanbrs1H: 步进高度.
            isBeyond: 是否需要对每个方格中节点间的步进进行调整.
            nbrs12t: {alter12: [2, 5, 7, 8], ...} // 每个alter12出现的时间步.
            nbrs12List: [id1, id2, ...], leve == 2时有效.
          */
          let this_ = this;
          let sliceStartIdx = 0; // 时间区间的起始位置.
          // let sliceEndIdx = 0;
          if(this_.$store.getters.gettimeStepSlice.length > 0){
            sliceStartIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);
            // sliceEndIdx = this_.$store.getters.gettimeStepList.indexOf(timeInterval[1]);
          }
          // let DPforWH = null;
          // if(isBeyond){
          //   DPforWH = this_.computeBasedWHForTimeSlice(posNumAlter1, posNumAlter2, svgWidth, svgHeight); // {sliceStartIdx: [], ..., sliceEndIdx: []}
          // }          
          let linksList = []; // [{actorId: x, source: [x, x], target: [x, x]}, ...]
          for(let actorId in nbrs1t.pos){ // 计算alters1的追踪线坐标.                        
            let posList = nbrs1t.pos[actorId]; // [-1, -1, -1, -2, -2, -3]
            if(posList.length > 1){ // 出现不止一次.
              if(nbrs12List.length > 0){ // leve == 2时
                if(nbrs12List.indexOf(actorId) != -1){ // 属于alter12
                  let startIndex = nbrs1t.tslice[actorId][0];              
                  if(isBeyond){                
                    detanbrs1W = DPforWH[startIndex][0];
                    detanbrs1H = DPforWH[startIndex][1];                               
                  }
                  let sx = null, sy=null, tx = null, ty = null;
                  // 起点
                  if(nbrs12t[actorId].indexOf(startIndex) != -1){ // 既是alter1又是alter2.
                    if(posList[0] < 0){ // 在上面.
                      sx = svgWidth * (startIndex - sliceStartIdx) + svgWidth / 2 - detanbrs1W * posList[0];
                      sy = svgHeight / 2 + detanbrs1H * posList[0]; 
                    }else{ // 在下面
                      sx = svgWidth * (startIndex - sliceStartIdx) + svgWidth / 2 - detanbrs1W * posList[0];
                      sy = svgHeight / 2 + detanbrs1H * posList[0];
                      tx = svgWidth * (startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[0];
                      ty = svgHeight / 2 + detanbrs1H * posList[0];
                      linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                      sx = tx;
                      sy = ty;
                    }                             
                    
                  }else{ // 当前是alter1
                    if(posList[0] < 0){
                      sx = svgWidth * (startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[0];
                      sy = svgHeight / 2 + detanbrs1H * posList[0];
                      tx = svgWidth * (startIndex - sliceStartIdx) + svgWidth / 2 - detanbrs1W * posList[0];
                      ty = svgHeight / 2 + detanbrs1H * posList[0];
                      linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                      sx = tx;
                      sy = ty;
                    }else{
                      sx = svgWidth * (startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[0];
                      sy = svgHeight / 2 + detanbrs1H * posList[0];
                    }
                    
                  }             
                  tx = 0;
                  ty = 0;                
                  for(let idx = 1; idx < posList.length; idx++){
                    if(isBeyond){                
                      detanbrs1W = DPforWH[startIndex + idx][0];
                      detanbrs1H = DPforWH[startIndex + idx][1];                               
                    }
                    if(nbrs12t[actorId].indexOf(startIndex + idx) != -1){ // 当前是alter2
                      if(posList[idx] < 0){ // 在上面
                        tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[idx];
                        ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                        linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                        sx = tx;
                        sy = ty;
                        tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 - detanbrs1W * posList[idx];
                        ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                        linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                      }else{ // 在下面.
                        tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 - detanbrs1W * posList[idx];
                        ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                        linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                        if(idx < posList.length - 1){ // 避免最后一个画线.
                          sx = tx;
                          sy = ty;
                          tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[idx];
                          ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                          linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                        }                        
                      }
                    }else{ // 当前是alter1
                      if(posList[idx] < 0){ // 上面
                        tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[idx];
                        ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                        linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                        if(idx < posList.length - 1){
                          sx = tx;
                          sy = ty;
                          tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 - detanbrs1W * posList[idx];
                          ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                          linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                        }                        
                      }else{ // 下面
                        tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 - detanbrs1W * posList[idx];
                        ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                        linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                        // if(idx < posList.length - 1){ // 避免最后一个画线.
                        sx = tx;
                        sy = ty;
                        tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[idx];
                        ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                        linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                        // }
                      }                 
                      
                    }
                    sx = tx;
                    sy = ty;                    
                  }                
                  
                }else{ // leve == 2, 只属于alter1
                  let startIndex = nbrs1t.tslice[actorId][0];              
                  if(isBeyond){                
                    detanbrs1W = DPforWH[startIndex][0];
                    detanbrs1H = DPforWH[startIndex][1];                               
                  }
                  let sx = null, sy=null, tx = null, ty = null;              
                  if(posList[0] < 0){
                      sx = svgWidth * (startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[0];
                      sy = svgHeight / 2 + detanbrs1H * posList[0];
                      tx = svgWidth * (startIndex - sliceStartIdx) + svgWidth / 2 - detanbrs1W * posList[0];
                      ty = svgHeight / 2 + detanbrs1H * posList[0];
                      linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                      sx = tx;
                      sy = ty;
                    }else{
                      sx = svgWidth * (startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[0];
                      sy = svgHeight / 2 + detanbrs1H * posList[0];
                    }                  
                  tx = 0;
                  ty = 0;                  
                  for(let idx = 1; idx < posList.length; idx++){
                    if(isBeyond){
                     detanbrs1W = DPforWH[startIndex + idx][0];
                     detanbrs1H = DPforWH[startIndex + idx][1]; 
                    }                    
                    if(posList[idx] < 0){ // 上面
                        tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[idx];
                        ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                        linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                        if(idx < posList.length - 1){
                          sx = tx;
                          sy = ty;
                          tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 - detanbrs1W * posList[idx];
                          ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                          linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                        }                        
                      }else{ // 下面
                        tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 - detanbrs1W * posList[idx];
                        ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                        linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                        // if(idx < posList.length - 1){ // 避免最后一个画线.
                        sx = tx;
                        sy = ty;
                        tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[idx];
                        ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                        linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                        // }
                      }
                      sx = tx;
                      sy = ty;
                  }
                }
              }else{ // level == 1
                let startIndex = nbrs1t.tslice[actorId][0];              
                  if(isBeyond){                
                    detanbrs1W = DPforWH[startIndex][0];
                    detanbrs1H = DPforWH[startIndex][1];                               
                  }              
                  let sx = svgWidth * (startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[0];
                  let sy = svgHeight / 2 + detanbrs1H * posList[0];              
                  let tx = 0;
                  let ty = 0;
                  // for(let idx = 1; idx < posList.length; idx++){
                  if(isBeyond){
                    for(let idx = 1; idx < posList.length; idx++){                  
                      detanbrs1W = DPforWH[startIndex + idx][0];
                      detanbrs1H = DPforWH[startIndex + idx][1];
                      tx = svgWidth * (idx + startIndex - sliceStartIdx) + svgWidth / 2 + detanbrs1W * posList[idx];
                      ty = svgHeight / 2 + detanbrs1H * posList[idx];  
                      linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                      sx = tx;
                      sy = ty;
                    }                  
                  }
                  else{
                    for(let idx = 1; idx < posList.length; idx++){
                      // 下面这个公式得改一改, 先吃饭, 待会再搞.
                      tx = sx + svgWidth + detanbrs1W * (posList[idx] - posList[idx - 1]);
                      ty = sy + detanbrs1H * (posList[idx] - posList[idx - 1]);
                      linksList.push({actorId: actorId, source: [sx, sy], target: [tx, ty]});
                      sx = tx;
                      sy = ty;
                    }                  
                  }
              }              
            }
          }
          if(egots[0] < egots[1]){ // 不只一个, 计算ego的追踪线坐标.
             for(let idx = egots[0]; idx <= egots[1] - 1; idx++){
                let sx = svgWidth * (idx - sliceStartIdx) + svgWidth / 2;
                let tx = svgWidth * (idx + 1 - sliceStartIdx) + svgWidth / 2;
                linksList.push({actorId: ego, source: [sx, svgHeight / 2], target: [tx, svgHeight / 2]});
             }
          }          
          return linksList;
       },
       drawnbrs1TrackLinks(selectorTrackg, linksList){ // computenbrs1TrackLinks(nbrs1t, svgWidth, svgHeight, detanbrs1W, detanbrs1H)
          let this_ = this;
          ////使用line元素.
          let trackLinks = d3.select(selectorTrackg).selectAll("line")
                                   .data(linksList) // [{source: x, target: x, weight: x}, ...]
                                   .enter().append("line")
                                   .attr("class", function(d){
                                      return "act-track-path " + "tractp-" + d.actorId.replace(/\./g, "-");
                                   })
                                   .attr("x1", function(d){return d.source[0];})
                                   .attr("y1", function(d){return d.source[1];})
                                   .attr("x2", function(d){return d.target[0]})
                                   .attr("y2", function(d){return d.target[1]})                                   
                                   .attr("stroke", "#d3d3d3")                                         
                                   .attr("stroke-width", 2);
          return trackLinks;
       },       
       layoutEgonet(timeStepIdx, egograph, nbrs1t, detanbrs1W, detanbrs1H, selectedPath, svgWidth, svgHeight, nbrLevel, actorR, trackLinks, curRowSelector, egoId, isBeyond=false, DPforWH=null, nbrs12List=null){ // 当前处于一个方格当中.
          /*
          功能: 为当前时间步布局snapshot.
          针对一个格子中1-level邻居或2-level邻居的布局.
           timeStepIdx: 在整个时间轴上的位置.
           egograph: {nodes: {ego: {id: x, name: x}, nbrs1: [{id: x, name: x}, ...], nbrs2: [{id: x, name: x}, ...]}, links: {nbrs1: [{}, ...], nbrs2: [{}, ...]}},
           selectedPath: 将要布局的格子,
           svgWidth: 格子的宽,
           svgHeight: 格子的高,
           nbrLevel: 邻居层数,
           detanbrs1W: 步进宽度,
           detanbrs1H: 步进高度,
           nbrs1t: {pos: {a1: [-1, -2, -1], ...}, tslice: {a1: [4, 6], ...}}, // 1-level邻居的布局位置(pos), 以及起始和终止时间(tslice). 
           isBeyond: 是否超出界限, false: 没有超出, true: 超出界限.
         */
          let this_ = this;         
          let grid = d3.select(selectedPath);          
          if(isBeyond){ // 更新 detanbrs1W detanbrs1H
            detanbrs1W = DPforWH[timeStepIdx][0];
            detanbrs1H = DPforWH[timeStepIdx][1];
          }
          // 颜色映射START
          let val2Color = null;
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
          // let fisheye = d3.fisheye.circular().radius(120); // 鱼眼.
          if(nbrLevel == 1){ // 1-level alters
            if(svgWidth == svgHeight){ // 方格
              let nbrs1 = JSON.parse(JSON.stringify(egograph.nodes.nbrs1)); // 拷贝一份
              if(nbrs1.length > 0){
                nbrs1.push(JSON.parse(JSON.stringify(egograph.nodes.ego))); // 拷贝一份, nbrs1=[{id: x, name: xx}, ..., {id:ego, name:egoname}]  
              }                            
              let actorsPos = {}; // {id: [x, y], ...}
              if(nbrs1.length > 0){
                nbrs1.forEach(function(d){
                  let actorId = d.id;                                  
                  let actorX = 0;
                  let actorY = 0;
                  if(actorId != egograph.nodes.ego.id){ // 1-level alters节点
                    let startIdx = nbrs1t.tslice[actorId][0];
                    let endIdx = nbrs1t.tslice[actorId][1];
                    if(timeStepIdx - startIdx >= 0 && endIdx - timeStepIdx >= 0){                                                                     
                      actorX = svgWidth / 2 + detanbrs1W * nbrs1t.pos[actorId][timeStepIdx - startIdx];
                      actorY = svgHeight / 2 + detanbrs1H * nbrs1t.pos[actorId][timeStepIdx - startIdx];                                      
                    }
                  }else{ // ego节点                                   
                    actorX = svgWidth / 2;
                    actorY = svgHeight / 2;
                  }
                  actorsPos[actorId] = [actorX, actorY];
                });
              }
              // 先绘制边, 然后绘制节点.
              let links = grid.append("g")
                              .attr("class", "links");
              let nbrs1links = links.append("g")
                                    .attr("class", "nbrs1-links")
                                    .selectAll("path")
                                    .data(egograph.links.nbrs1) // [{source: x, target: x, weight: x}, ...]
                                    .enter().append("path")
                                    .attr("class", "link-path")
                                    .attr('d', function (d) {
                                      let sx = actorsPos[d.source][0];
                                      let sy = actorsPos[d.source][1];
                                      let tx = actorsPos[d.target][0];
                                      let ty = actorsPos[d.target][1];
                                      let ctrX = 0;
                                      let ctrY = 0;
                                      if(sx < tx){
                                        ctrX = tx;
                                        ctrY = sy;
                                      }else{
                                        ctrX = sx;
                                        ctrY = ty;
                                      }                                      
                                      let dStr = ['M', sx, sy,
                                        'Q', ctrX, ctrY, ',',   
                                        tx, ty].join(' ');
                                      return dStr;
                                    })                                    
                                    .attr("fill", "none")
                                    .attr("stroke", "grey")
                                    .attr("stroke-width", function(d){
                                      return Math.sqrt(d.weight);
                                    })
                                    .attr("display", "none");
              // 先绘制边, 然后绘制节点, 这样使节点盖住边.
              let alters = grid.append("g")
                               .attr("class", "nodes");            
              let nbrs1alters = alters.append("g")
                                .attr("class", "nbrs1-alters")
                                .selectAll("g")
                                .data(nbrs1) // [{id: x, name: xx}, ...]
                                .enter().append("g")
                                .attr("class", "node")
                                .attr("transform", function(d){                                  
                                  let actorId = d.id;
                                  return "translate(" + actorsPos[actorId][0] + "," + actorsPos[actorId][1] + ")";                                
                                });            
              // console.log("actorsPos");console.log(actorsPos);
              // 节点形状
              let nbrs1circles = nbrs1alters.append("circle")                                                                          
                                .attr("class", function(d){                                  
                                  let nodeClassStr = d.id.replace(/\./g, "-");
                                  return "nodecircle" + " " + "dyegovis-" + nodeClassStr;  // 以节点id作为circle标签的class之一.
                                })
                                .attr("r", function(d){
                                  return actorR;
                                })
                                .attr("stroke", "#d1d1d1") // fixme: 中期时加的
                                .attr("stroke-width", 1) // fixme: 中期时加的
                                .attr("fill", function(d) {
                                  let attrVal = d[this_.$store.getters.getattrRadio]; 
                                  if(this_.$store.getters.getattrRadio == "position"){                                    
                                    return val2Color[attrVal]; 
                                  }else{                                                                         
                                    return val2Color(attrVal);
                                  }                                           
                                });

              let nbrs1lables = nbrs1alters.append("text")  // 显示节点的标签.
                                      .text(function(d) {                                          
                                          if(this_.$store.getters.getselectedDataset == "enron"){
                                            return d.name + "(" + d.position + ")";
                                          }
                                          if(this_.$store.getters.getselectedDataset == "tvcg"){
                                            return d.name;
                                          }                                         
                                      })
                                      .attr('x', function(d){
                                        // console.log("maotingyun text"); console.log(d);
                                        return actorR + 1;
                                      })
                                      .attr("display", "none")
                                      .attr("font-size", 12) // fixme: 中期时加的
                                      .attr('y', -2);
              // 焦点上方添加一个标志点.
              nbrs1alters.filter(function (d){
                      return d.id == egoId; // the first dot.
                   })
                   .append("circle")
                      .attr("cx", 0)
                      .attr("cy", function(d){
                         return -7;
                      })
                      .attr('r', 2) // 标记点的半径
                      .attr("class", "slt-ego-node")
                      .attr('fill', function (d) {
                          let idx = this_.$store.getters.getselectedEgoList.indexOf(egoId);
                          return this_.$store.getters.getcolorSchemeList[idx];
                      });
              nbrs1circles.on("click", function(d){ // 1-level alters 点击事件.
                let curId = d.id;
                if(this_.clickActorSet.hasOwnProperty(egoId)){ // 已经存在
                  if(this_.clickActorSet[egoId].indexOf(curId) == -1){ // 当前行没有点击过该节点,则高亮该节点对应的节点及其追踪线.
                      if(nbrs1t.tslice[curId][0] != nbrs1t.tslice[curId][1]){
                        this_.clickActorSet[egoId].push(curId);
                        // console.log("this_.clickActorSet");console.log(this_.clickActorSet);
                        d3.selectAll(curRowSelector + " .nodecircle").filter(function(fd){
                          return fd.id == curId;
                        }).attr("stroke", "#de2d26");                      
                        trackLinks.filter(function(ld){
                          return ld.actorId == curId;
                        }).attr('stroke', "#de2d26");
                      }                      
                  }else{ // 当前行中的节点已经点击过, 高亮失效.                   
                      let indexR = this_.clickActorSet[egoId].indexOf(curId); // 已经
                      this_.clickActorSet[egoId].splice(indexR, 1);
                      // console.log("this_.clickActorSet");console.log(this_.clickActorSet);
                      d3.selectAll(curRowSelector + " .nodecircle").filter(function(fd){
                        return fd.id == curId;
                      }).attr('stroke', "#d1d1d1");                     
                      trackLinks.filter(function(ld){
                        return ld.actorId == curId;
                      }).attr('stroke', "#d3d3d3");               
                  }
                }else{ // 还没有, 第一次点击, 颜色高亮.
                  if(nbrs1t.tslice[curId][0] != nbrs1t.tslice[curId][1]){ // 保证是持续点.
                      this_.clickActorSet[egoId] = [curId]; // {ego: [x]}
                      // console.log("this_.clickActorSet");console.log(this_.clickActorSet);
                      d3.selectAll(curRowSelector + " .nodecircle").filter(function(fd){                            
                            return fd.id == curId;
                      }).attr("stroke", "#de2d26");                     
                      trackLinks.filter(function(ld){
                        return ld.actorId == curId;
                      }).attr('stroke', "#de2d26");
                  }                  
                }               

              });
              nbrs1circles.on("mouseover", function(d){ // 1-level alters 悬浮事件.                                          
                let curId = d.id;
                d3.selectAll(curRowSelector + " .nodecircle").style('opacity', .1); // 整行节点透明.
                d3.selectAll(curRowSelector + " .slt-ego-node").style('opacity', .4); // 标记节点透明.
                d3.selectAll(curRowSelector + " .nodecircle").filter(function(alld){ // 整行当前悬浮节点高亮, 其他所有节点透明.                  
                  return alld.id == curId;
                }).style('opacity', 1);
                d3.selectAll(curRowSelector + " .slt-ego-node").filter(function(alld){ // 整行当前悬浮节点高亮, 其他所有节点透明.                  
                  // console.log("alld curRowSelector"); console.log(alld);
                  return alld.id == curId;
                }).style('opacity', 1);
                trackLinks.style('opacity', .1); // 所有的追踪线透明.
                trackLinks.filter(function(ld){ // 当前悬浮节点的追踪线高亮, 其余透明
                  return ld.actorId == curId;
                }).style('opacity', 1);                
                nbrs1lables.attr("display", function(dd){ // 显示标签.
                  return dd.id == curId ? "block": "none";                 
                });
                let stSet = new Set();
                nbrs1links.attr("display", function(lk){ // 悬浮节点对应的所有边高亮. lk={source: x, target: x, weight: x}
                  let sid = lk.source;
                  let tid = lk.target;
                  if(sid == curId){                    
                    stSet.add(tid);
                    return "block";
                  }
                  if(tid == curId){
                    stSet.add(sid);
                    return "block";
                  }
                  return "none";
                });
               d3.selectAll("#svg-dyegonet #gcompLines .act-comp-path").style('opacity', 0.1);
               nbrs1circles.filter(function(f){ // 悬浮节点对应边的端点节点高亮.
                  if(stSet.has(f.id)){
                    // d3.selectAll("#svg-dyegonet #gcompLines .compl-" + f.id.replace(/\./g, "-") + "[name='" + this_.$store.getters.gettimeStepList[timeStepIdx] +  "']").style('opacity', 1); // 端点的对比线也高亮.
                    return true;
                  }                  
                }).style('opacity', 1);
                nbrs1lables.filter(function(f){ // 悬浮节点对应边的端点节点的标签高亮.
                  return stSet.has(f.id);
                }).attr("display", "block");                
                // d3.selectAll("#svg-dyegonet #gcompLines .act-comp-path").style('opacity', 0.1);
                d3.selectAll("#svg-dyegonet #gcompLines .compl-" + curId.replace(/\./g, "-")).style('opacity', 1);
                // kevin.presto
                // if(this_.$store.getters.getselectedDataset == "enron"){
                d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-at-timestep circle[name='" + curId + "'").attr("fill", "#de2d26");
                d3.select("#ego-overview-box circle." + "dyegovis-" + curId.replace(/\./g, "-")).attr("fill", this_.$store.getters.getcolorMap.egoColor);
                // }
                                    
              }).on("mouseout", function(d){
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
                d3.selectAll(curRowSelector + " .nodecircle").style('opacity', 1); // 整行节点恢复.
                d3.selectAll(curRowSelector + " .slt-ego-node").style('opacity', 1); //  标记节点恢复.
                trackLinks.style('opacity', 1);
                nbrs1lables.attr("display", "none");
                nbrs1links.attr("display", "none");
                d3.selectAll("#svg-dyegonet #gcompLines .act-comp-path").style('opacity', 1);
                // if(this_.$store.getters.getselectedDataset == "enron"){
                d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-at-timestep circle[name='" + d.id + "'").attr("fill", function(){
                  // this_.$store.getters.getcolorMap.pointColorObj[d.position]                    
                  let attrVal = d[this_.$store.getters.getattrRadio]; 
                  if(this_.$store.getters.getattrRadio == "position"){                                    
                    return val2Color[attrVal]; 
                  }else{                                                                        
                    return val2Color(attrVal);
                  }
                });
                d3.select("#ego-overview-box circle." + "dyegovis-" + d.id.replace(/\./g, "-")).attr("fill", function(){            
                  let attrVal = d[this_.$store.getters.getattrRadio]; 
                  if(this_.$store.getters.getattrRadio == "position"){                                    
                    return val2Color[attrVal]; 
                  }else{ 
                    // console.log("mouseout val2Color"); console.log(val2Color);                                                           
                    return val2Color(attrVal);
                  }
                });
                // }
                
              });
              // 添加鱼眼技术              
              // grid.on("mouseover", function(){
              //   fisheye.focus(d3.mouse(this));
              //   nbrs1alters.each(function(d) { d.fisheye = fisheye(d); })
              //              .attr("transform", function(d){                             
              //                 return "translate(" + d.fisheye.x + "," + d.fisheye.y + ")";  
              //              });

              // });
              return nbrs1circles;
            }
          }
          if(nbrLevel == 2){
            if(svgWidth == svgHeight){ // 方格
              let nbrs1 = JSON.parse(JSON.stringify(egograph.nodes.nbrs1)); // 拷贝一份 [{id:x, name: x, ...}, ...]
              let nbrs2 = JSON.parse(JSON.stringify(egograph.nodes.nbrs2)); // 拷贝一份 [{id:x, name: x, ...}, ...]
              // let nbrs12 = nbrs12List;
              if(nbrs1.length > 0){
                nbrs1.push(JSON.parse(JSON.stringify(egograph.nodes.ego))); // 拷贝一份, nbrs1=[{id: x, name: xx}, ..., {id:ego, name:egoname}]  
              }
              let curTimestepNodeList = []; // 当前时间步下的节点.                            
              let actorsPos = {}; // {id: [x, y], ...}              
              if(nbrs1.length > 0){
                nbrs1.forEach(function(d){
                  let actorId = d.id;                                  
                  let actorX = 0;
                  let actorY = 0;
                  if(actorId != egograph.nodes.ego.id){ // 1-level alters节点
                    curTimestepNodeList.push(actorId);
                    let startIdx = nbrs1t.tslice[actorId][0];
                    let endIdx = nbrs1t.tslice[actorId][1];
                    if(timeStepIdx - startIdx >= 0 && endIdx - timeStepIdx >= 0){                                                                     
                      actorX = svgWidth / 2 + detanbrs1W * nbrs1t.pos[actorId][timeStepIdx - startIdx];
                      actorY = svgHeight / 2 + detanbrs1H * nbrs1t.pos[actorId][timeStepIdx - startIdx];                                      
                    }
                  }else{ // ego节点                                   
                    actorX = svgWidth / 2;
                    actorY = svgHeight / 2;
                  }
                  actorsPos[actorId] = [actorX, actorY];
                });
              }
              // nbrs12List
              let curnbrs12 = []; // 当前时间步下, alter2中属于alter12的节点.
              if(nbrs2.length > 0){
                nbrs2.forEach(function(d){
                  let actorId = d.id;
                  if(nbrs12List.indexOf(actorId) != -1){ // nbrs12List = [x, x, x, ...], 说明该节点是属于nbrs12, 即能够转化成1-degree的alter2.
                    let actorX = 0;
                    let actorY = 0;                    
                    if(actorId != egograph.nodes.ego.id){ // 1-level alters节点
                      // console.log("jjjjjj nbrs2");
                      curnbrs12.push(d); // [{id:x, ...}, ...]
                      curTimestepNodeList.push(actorId);
                      let startIdx = nbrs1t.tslice[actorId][0];
                      let endIdx = nbrs1t.tslice[actorId][1];
                      if(timeStepIdx - startIdx >= 0 && endIdx - timeStepIdx >= 0){                                                                     
                        actorX = svgWidth / 2 - detanbrs1W * nbrs1t.pos[actorId][timeStepIdx - startIdx];
                        actorY = svgHeight / 2 + detanbrs1H * nbrs1t.pos[actorId][timeStepIdx - startIdx];                                      
                      }
                    }else{ // ego节点                                   
                      actorX = svgWidth / 2;
                      actorY = svgHeight / 2;
                    }
                    actorsPos[actorId] = [actorX, actorY];
                  }
                });
              }
              let edgeBnbrs12List = [];
              if(egograph.links.nbrs2.length > 0){
                edgeBnbrs12List = egograph.links.nbrs2.filter(function(d){ // d = {source: x, target: x, ...} 
                  if(curTimestepNodeList.indexOf(d.source) != -1 && curTimestepNodeList.indexOf(d.target) != -1){
                    return true;
                  }
                });
              }
               
              // 先绘制边, 然后绘制节点.
              let links = grid.append("g")
                              .attr("class", "links");
              let nbrs1links = links.append("g")
                                    .attr("class", "nbrs1-links")
                                    .selectAll("path")
                                    .data(egograph.links.nbrs1.concat(edgeBnbrs12List)) // [{source: x, target: x, weight: x}, ...]
                                    .enter().append("path")
                                    .attr("class", "link-path")
                                    .attr('d', function (d) {
                                      let sx = actorsPos[d.source][0];
                                      let sy = actorsPos[d.source][1];
                                      let tx = actorsPos[d.target][0];
                                      let ty = actorsPos[d.target][1];
                                      let ctrX = 0;
                                      let ctrY = 0;
                                      if(sx < tx){
                                        ctrX = tx;
                                        ctrY = sy;
                                      }else{
                                        ctrX = sx;
                                        ctrY = ty;
                                      }                                      
                                      let dStr = ['M', sx, sy,
                                        'Q', ctrX, ctrY, ',',   
                                        tx, ty].join(' ');
                                      return dStr;
                                    })                                    
                                    .attr("fill", "none")
                                    .attr("stroke", "grey")
                                    .attr("stroke-width", function(d){
                                      return Math.sqrt(d.weight);
                                    })
                                    .attr("display", "none");
              // 先绘制边, 然后绘制节点, 这样使节点盖住边.
              let alters = grid.append("g")
                               .attr("class", "nodes");            
              let nbrs1alters = alters.append("g")
                                .attr("class", "nbrs1-alters")
                                .selectAll("g")
                                .data(nbrs1.concat(curnbrs12)) // [{id: x, name: xx}, ...]
                                .enter().append("g")
                                .attr("class", "node")
                                .attr("transform", function(d){                                  
                                  let actorId = d.id;
                                  return "translate(" + actorsPos[actorId][0] + "," + actorsPos[actorId][1] + ")";                                
                                });            
              // console.log("actorsPos");console.log(actorsPos);
              // 节点形状
              let nbrs1circles = nbrs1alters.append("circle")                                                                          
                                .attr("class", function(d){                                  
                                  let nodeClassStr = d.id.replace(/\./g, "-");
                                  return "nodecircle" + " " + "dyegovis-" + nodeClassStr;  // 以节点id作为circle标签的class之一.
                                })
                                .attr("r", function(d){
                                  return actorR;
                                })
                                .attr("stroke", "#d1d1d1") // fixme: 中期时加的
                                .attr("stroke-width", 1) // fixme: 中期时加的
                                .attr("fill", function(d) {
                                  let attrVal = d[this_.$store.getters.getattrRadio]; 
                                  if(this_.$store.getters.getattrRadio == "position"){                                    
                                    return val2Color[attrVal]; 
                                  }else{                                                                         
                                    return val2Color(attrVal);
                                  }                                           
                                });

              let nbrs1lables = nbrs1alters.append("text")  // 显示节点的标签.
                                      .text(function(d) {                                          
                                          if(this_.$store.getters.getselectedDataset == "enron"){
                                            return d.name + "(" + d.position + ")";
                                          }
                                          if(this_.$store.getters.getselectedDataset == "tvcg"){
                                            return d.name;
                                          }                                         
                                      })
                                      .attr('x', function(d){
                                        // console.log("maotingyun text"); console.log(d);
                                        return actorR + 4;
                                      })
                                      .attr("display", "none")
                                      .attr("font-size", 12) // fixme: 中期时加的
                                      .attr('y', 3);
              // 焦点上方添加一个标志点.
              nbrs1alters.filter(function (d){
                      return d.id == egoId; // the first dot.
                   })
                   .append("circle")
                      .attr("cx", 0)
                      .attr("cy", function(d){
                         return -7;
                      })
                      .attr('r', 2) // 标记点的半径
                      .attr("class", "slt-ego-node")
                      .attr('fill', function (d) {
                          let idx = this_.$store.getters.getselectedEgoList.indexOf(egoId);
                          return this_.$store.getters.getcolorSchemeList[idx];
                      });
              nbrs1circles.on("click", function(d){ // 1-level alters 点击事件.
                let curId = d.id;
                if(this_.clickActorSet.hasOwnProperty(egoId)){ // 已经存在
                  if(this_.clickActorSet[egoId].indexOf(curId) == -1){ // 当前行没有点击过该节点,则高亮该节点对应的节点及其追踪线.
                      if(nbrs1t.tslice[curId][0] != nbrs1t.tslice[curId][1]){
                        this_.clickActorSet[egoId].push(curId);
                        // console.log("this_.clickActorSet");console.log(this_.clickActorSet);
                        d3.selectAll(curRowSelector + " .nodecircle").filter(function(fd){
                          return fd.id == curId;
                        }).attr("stroke", "#de2d26");                      
                        trackLinks.filter(function(ld){
                          return ld.actorId == curId;
                        }).attr('stroke', "#de2d26");
                      }                      
                  }else{ // 当前行中的节点已经点击过, 高亮失效.                   
                      let indexR = this_.clickActorSet[egoId].indexOf(curId); // 已经
                      this_.clickActorSet[egoId].splice(indexR, 1);
                      // console.log("this_.clickActorSet");console.log(this_.clickActorSet);
                      d3.selectAll(curRowSelector + " .nodecircle").filter(function(fd){
                        return fd.id == curId;
                      }).attr('stroke', "#d1d1d1");                     
                      trackLinks.filter(function(ld){
                        return ld.actorId == curId;
                      }).attr('stroke', "#d3d3d3");               
                  }
                }else{ // 还没有, 第一次点击, 颜色高亮.
                  if(nbrs1t.tslice[curId][0] != nbrs1t.tslice[curId][1]){ // 保证是持续点.
                      this_.clickActorSet[egoId] = [curId]; // {ego: [x]}
                      // console.log("this_.clickActorSet");console.log(this_.clickActorSet);
                      d3.selectAll(curRowSelector + " .nodecircle").filter(function(fd){                            
                            return fd.id == curId;
                      }).attr("stroke", "#de2d26");                     
                      trackLinks.filter(function(ld){
                        return ld.actorId == curId;
                      }).attr('stroke', "#de2d26");
                  }                  
                }               

              });
              nbrs1circles.on("mouseover", function(d){ // 1-level alters 悬浮事件.                                          
                let curId = d.id;
                d3.selectAll(curRowSelector + " .nodecircle").style('opacity', .1); // 整行节点透明.
                d3.selectAll(curRowSelector + " .slt-ego-node").style('opacity', .4); // 标记节点透明.
                d3.selectAll(curRowSelector + " .nodecircle").filter(function(alld){ // 整行当前悬浮节点高亮, 其他所有节点透明.                  
                  return alld.id == curId;
                }).style('opacity', 1);
                d3.selectAll(curRowSelector + " .slt-ego-node").filter(function(alld){ // 整行当前悬浮节点高亮, 其他所有节点透明.                  
                  // console.log("alld curRowSelector"); console.log(alld);
                  return alld.id == curId;
                }).style('opacity', 1);
                trackLinks.style('opacity', .1); // 所有的追踪线透明.
                trackLinks.filter(function(ld){ // 当前悬浮节点的追踪线高亮, 其余透明
                  return ld.actorId == curId;
                }).style('opacity', 1);                
                nbrs1lables.attr("display", function(dd){ // 显示标签.
                  return dd.id == curId ? "block": "none";                 
                });
                let stSet = new Set();
                nbrs1links.attr("display", function(lk){ // 悬浮节点对应的所有边高亮. lk={source: x, target: x, weight: x}
                  let sid = lk.source;
                  let tid = lk.target;
                  if(sid == curId){                    
                    stSet.add(tid);
                    return "block";
                  }
                  if(tid == curId){
                    stSet.add(sid);
                    return "block";
                  }
                  return "none";
                });
               nbrs1circles.filter(function(f){ // 悬浮节点对应边的端点节点高亮.
                  return stSet.has(f.id);
                }).style('opacity', 1);
                nbrs1lables.filter(function(f){ // 悬浮节点对应边的端点节点的标签高亮.
                  return stSet.has(f.id);
                }).attr("display", "block");                
                d3.selectAll("#svg-dyegonet #gcompLines .act-comp-path").style('opacity', 0.1);
                d3.selectAll("#svg-dyegonet #gcompLines .compl-" + curId.replace(/\./g, "-")).style('opacity', 1);
                // kevin.presto
                // if(this_.$store.getters.getselectedDataset == "enron"){
                d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-at-timestep circle[name='" + curId + "'").attr("fill", "#de2d26");
                d3.select("#ego-overview-box circle." + "dyegovis-" + curId.replace(/\./g, "-")).attr("fill", this_.$store.getters.getcolorMap.egoColor);
                // }
                                    
              }).on("mouseout", function(d){
                // 颜色映射START
                let val2Color = null;
                // console.log("this_.$store.getters.getattrRadio"); console.log(this_.$store.getters.getattrRadio);
                if(this_.$store.getters.getattrRadio == "position"){
                  // val2Color = this_.$store.getters.getcolorMap.pointColorObj; // this_.$store.getters.getcolorRadio
                  val2Color = this_.$store.getters.getcolorMap.pointColorShObj[this_.$store.getters.getcolorRadio];
                }else{
                  let minMaxVal = this_.$store.getters.getfilterObj[this_.$store.getters.getattrRadio]; // [min, max]
                  let colorList = this_.$store.getters.getcolorSchemeObj[this_.$store.getters.getcolorRadio];
                  let colorScheme = [colorList[0], colorList[colorList.length - 1]];        
                  val2Color = d3.scaleLinear().domain(minMaxVal)
                                    .range(colorScheme);
                }        
                // 颜色映射END               
                d3.selectAll(curRowSelector + " .nodecircle").style('opacity', 1); // 整行节点恢复.
                d3.selectAll(curRowSelector + " .slt-ego-node").style('opacity', 1); //  标记节点恢复.
                trackLinks.style('opacity', 1);
                nbrs1lables.attr("display", "none");
                nbrs1links.attr("display", "none");
                d3.selectAll("#svg-dyegonet #gcompLines .act-comp-path").style('opacity', 1);
                // if(this_.$store.getters.getselectedDataset == "enron"){
                d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-at-timestep circle[name='" + d.id + "'").attr("fill", function(){
                  // this_.$store.getters.getcolorMap.pointColorObj[d.position]                    
                  let attrVal = d[this_.$store.getters.getattrRadio]; 
                  if(this_.$store.getters.getattrRadio == "position"){                                    
                    return val2Color[attrVal]; 
                  }else{                                                                        
                    return val2Color(attrVal);
                  }
                });
                d3.select("#ego-overview-box circle." + "dyegovis-" + d.id.replace(/\./g, "-")).attr("fill", function(){            
                  let attrVal = d[this_.$store.getters.getattrRadio]; 
                  if(this_.$store.getters.getattrRadio == "position"){                                    
                    return val2Color[attrVal]; 
                  }else{ 
                    // console.log("mouseout val2Color"); console.log(val2Color);                                                           
                    return val2Color(attrVal);
                  }
                });
                // }
                
              });
              // 添加鱼眼技术              
              // grid.on("mouseover", function(){
              //   fisheye.focus(d3.mouse(this));
              //   nbrs1alters.each(function(d) { d.fisheye = fisheye(d); })
              //              .attr("transform", function(d){                             
              //                 return "translate(" + d.fisheye.x + "," + d.fisheye.y + ")";  
              //              });

              // });
              return nbrs1circles;
            }
          }
       },
       callbackMouseout(egoId, nodeObj){
        let this_ = this;
        // 颜色映射START
        let val2Color = null;
        // console.log("SmallMultiple mouseout");
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
        d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-at-timestep circle[name='" + egoId + "'").attr("fill", function(){
            // console.log("SmallMultiple mouseout svg-egonets-time-step");
            let attrVal = nodeObj[this_.$store.getters.getattrRadio]; 
            if(this_.$store.getters.getattrRadio == "position"){                                    
              return val2Color[attrVal]; 
            }else{                                                                        
              return val2Color(attrVal);
            }
        });
        d3.select("#ego-overview-box circle." + "dyegovis-" + egoId.replace(/\./g, "-")).attr("fill", function(){            
            // console.log("SmallMultiple mouseout ego-overview-box");
            let attrVal = nodeObj[this_.$store.getters.getattrRadio]; 
            if(this_.$store.getters.getattrRadio == "position"){                                    
              return val2Color[attrVal]; 
            }else{                                                                    
              return val2Color(attrVal);
            }
        });
       },       
       reRenderDyEgonet(selectedEgoId){
          let this_ = this;
          // 删除nodes和links.         
          // fixme: 绘制行 + 时间步格子后,将每个时间步对应的egonet绘制到响应的格子中.
          let timeInterval = this_.$store.getters.gettimeStepSlice; // [2000-02, 2002-01]
          let timeStepList = this_.$store.getters.gettimeStepList; // [x, x, ...]
          if(timeStepList[0] == timeInterval[0] && timeStepList[timeStepList.length - 1] == timeInterval[1]){
             timeInterval = [];
          }
          let param = {dbname: this_.$store.getters.getselectedDataset, timeInterval: timeInterval, ego: selectedEgoId, egonetLevel1: this_.egonetLevel1}; // ego: curVal[curVal.length - 1] 
          /* 说明: 当用户点击一个节点时, 先在svg中绘制一行, 然后在这一行中根据时间步数绘制格子,最后拿着id向后台请求对应的egonet, 响应后, 先找到对应的行, 然后找到对应的格子并将egonet布局在格子中.
          */
          axios.post(vueFlaskRouterConfig.selecteddyegonet, { // 请求ego对应的序列.
             param: JSON.stringify(param)
          })
          .then((res) => {
                  // console.log("click ego respond data"); console.log(res.data);
                  /*res.data:
                    {
                      dyegonet: {2000-03: {nodes: {ego: {id:x, name:x, ...}, nbrs1: [{}, ...], nbrs2: [{}, ...]}, links: {nbrs1: [{source: x, target: x, weight: x}, ...], nbrs2: [{}, ...]}}, ...},
                      nbrs1t: {pos: {a1: [-1, -2, -1], ...}, tslice: {a1: [4, 6], ...}}, // 1-level邻居的布局位置(pos), 以及起始和终止时间(tslice).
                      nbrs2t: {pos: {b1: [-1, -2, -1], ...}, tslice: {b1: [4, 6], ...}} // 2-level邻居的布局位置(pos), 以及起始和终止时间(tslice).
                      maxs1: x, // alter1偏离ego的最大位置
                      maxs2: x, // alter2偏离ego的最大位置
                      egots: [x, x] // dyegonet的时间切片, i.e., [start_time, end_time],
                      pos_num_alter1: [x, x, ...], // alter1的每个时间步下的位置数量, 用于调整每个方格的步进宽度和高度.
                      pos_num_alter2: [x, x, ...], // alter2的每个时间步下的位置数量, 用于调整每个方格的步进宽度和高度.
                      nbrs12: [x, ...]
                    }
                  */
                  let graph = res.data.dyegonet; // egonet序列. 
                  let nbrs1t = res.data.nbrs1t;
                  let nbrs1MaxSize = res.data.maxs1; // 当前动态egonet中最大的egonet.
                  let egots = res.data.egots; // [startTime, endTime]
                  let posNumAlter1 = res.data.pos_num_alter1;
                  let posNumAlter2 = res.data.pos_num_alter2;
                  let nbrs12List = res.data.nbrs12; // [x, x, x, ...]  
                  let nbrs12t = res.data.nbrs12t;
                  // console.log("nbrs1MaxSize");console.log(nbrs1MaxSize);
                  /*
                    graph = {2000-03: {nodes: {ego: {}, nbrs1: [{}, ...], nbrs2: [{}, ...]}, links: {nbrs1: [{}, ...], nbrs2: [{}, ...]}}, ...}
                  */                 
                  let isDirected = false;
                  let layoutSettings = null;
                  if(this_.layoutMethod == "SmallMultiple"){
                    layoutSettings = { // 布局参数设置.
                      linkLength: 10,
                      chargeStrength: -20,
                      edgeMode: "line",
                      labelDisplay: false,
                      limitBox: true,
                      nodeColor:"#FF8700",
                      radius: 5,
                      curDataset: this_.$store.getters.getselectedDataset,
                      egoId: selectedEgoId
                    };
                  }                                    
                  let svgWidth = this_.$store.getters.gettimeStepEgonetW;
                  let svgHeight = this_.$store.getters.gettimeStepEgonetH;                  
                  let selectorP = "#svg-dyegonet #all-dyegonets .each-dyegonet[name=" + "'" + selectedEgoId + "'" +  "]" + " .egonet-at-timestep"; // 找到序列所在的行.
                  let svgIdSelector = "#svg-dyegonet";
                  let selectElementName = d3.selectAll(selectorP)._groups[0]; // 时间步对应的元素: [g, g, ...]                  
                  //add let nbrs1t = res.data.nbrs1t;
                  let nbrs1WH = null; // 1-level的步进参数[W, H, isBeyond]
                  let DPforWH = null;
                  let trackLinks = null;
                  let curRowSelector = "#svg-dyegonet #all-dyegonets .each-dyegonet[name=" + "'" + selectedEgoId + "'" + "]"; // 当前所在行
                  // 先绘制线.
                  if(this_.layoutMethod == "noname"){
                    nbrs1WH = this_.computedetanbrs1H(nbrs1MaxSize, svgWidth, svgHeight); // 获得边与高的步进.
                    if(nbrs1WH[2]){
                      DPforWH = this_.computeBasedWHForTimeSlice(posNumAlter1, posNumAlter2, svgWidth, svgHeight); // {sliceStartIdx: [], ..., sliceEndIdx: []}
                    }
                    let linksList = this_.computenbrs1TrackLinks(nbrs1t, svgWidth, svgHeight, nbrs1WH[0], nbrs1WH[1], egots, selectedEgoId, nbrs1WH[2], DPforWH, nbrs12t, nbrs12List); // let nbrs12t = res.data.nbrs12t; // {id1: [1, 2, 4, 6], ...}, 每个alter12出现的时间步. 
                    let selectorTrackg = "#svg-dyegonet #all-dyegonets .each-dyegonet[name=" + "'" + selectedEgoId + "'" +  "]" + " .actor-track"; // 当前行所在的追踪线g.
                    trackLinks = this_.drawnbrs1TrackLinks(selectorTrackg, linksList); // 绘制追踪线.                                       
                  }                  
                  
                  // add
                  let nodecirclesList = [];
                  for(let i=0; i<selectElementName.length; i++){ // 一行中, 逐个绘制每个时间步的snapshot.
                    let eachElement = selectElementName[i];                    
                    let timeStep = eachElement.attributes[1].nodeValue; // 例如, "2000-03"
                    let selectedPath = "#svg-dyegonet #all-dyegonets .each-dyegonet[name=" + "'" + selectedEgoId + "'" + "]" + " .egonet-" + i; // 格子.
                    
                    if(this_.layoutMethod == "SmallMultiple"){
                      let egonetLen = 0;
                      if(graph[timeStep].nodes.nbrs1.length > 0){
                        egonetLen = graph[timeStep].nodes.nbrs1.length + graph[timeStep].nodes.nbrs2.length + 1;
                      }                    
                      if(egonetLen < 30){
                        layoutSettings.chargeStrength = -80;
                      }else{
                        layoutSettings.chargeStrength = -20;
                      }
                      // 颜色映射 Start
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
                      // 颜色映射 End  val2Color, this_.$store.getters.getattrRadio 
                      let nodecircles = d3GraphLayout(graph[timeStep], isDirected, layoutSettings, selectedPath, svgWidth, svgHeight, svgIdSelector, null, null, this_.callbackMouseOver, null, val2Color, this_.$store.getters.getattrRadio, this_.$store.getters.getselectedEgoList, this_.$store.getters.getcolorSchemeList, selectedEgoId, this_.callbackMouseout); // 力导引布局展示  
                      nodecirclesList.push(nodecircles);
                    }
                    if(this_.layoutMethod == "noname"){
                      let timeStepIdx = this_.$store.getters.gettimeStepList.indexOf(timeStep);
                      let sliceStartIdx = 0; // 时间区间的起始位置.          
                      if(this_.$store.getters.gettimeStepSlice.length > 0){
                        sliceStartIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);            
                      }
                      let nbrLevel = this_.egonetLevel1 ? 1 : 2; // 当前的层数.                    
                      let nodecircles = this_.layoutEgonet(timeStepIdx, graph[timeStep], nbrs1t, nbrs1WH[0], nbrs1WH[1], selectedPath, svgWidth, svgHeight, nbrLevel, 4, trackLinks, curRowSelector, selectedEgoId, nbrs1WH[2], DPforWH, nbrs12List);
                      // xxx
                      nodecirclesList.push(nodecircles); // let nodecircles
                    }                                     
                  }
                  if(this_.$store.getters.getselectedEgoList.length > 1){
                   // console.log("egonetseq-level-icon compareLineDraw in");
                   this_.compareLineDraw();
                  }
                  // 将 nodecirclesList 添加到全局数组中.
                  this_.$store.commit("addOneegoNetSequenceRt", nodecirclesList); // let nodecirclesList = []; nodecircles
                  //找到ego节点,并更改其颜色填充.
                  let curEgo = selectedEgoId; // curVal[curVal.length - 1];
                  let newEgoId = curEgo.split("."); // [x, x, ...]
                  let nodeClassStr = "";
                  if(newEgoId.length > 1){
                    let counter = newEgoId.length;
                    for(let i=0; i<counter; i++){
                        if(i<counter-1){
                          nodeClassStr = nodeClassStr + newEgoId[i] + "-";
                        }else{
                          nodeClassStr = nodeClassStr + newEgoId[i];
                        }
                    }
                  }
                  else{
                    nodeClassStr = newEgoId[0];
                  }                  
                  // d3.selectAll("#svg-dyegonet #all-dyegonets .each-dyegonet[name=" + "'" + selectedEgoId + "'" + "]" + " ." + "dyegovis-" + nodeClassStr).attr("fill", function (e){
                  //     let idx = this_.$store.getters.getselectedEgoList.indexOf(selectedEgoId);
                  //     return this_.$store.getters.getcolorSchemeList[idx];
                  // });
                  // d3.selectAll("#svg-dyegonet #all-dyegonets .each-dyegonet[name=" + "'" + selectedEgoId + "'" + "]" + " ." + "dyegovis-" + nodeClassStr)
                  //   .append("circle")
                  //   .attr("cx", 0)
                  //   .attr("cy", function(d){
                  //      return -6;
                  //   })
                  //   .attr('r', 3) // 标记点的半径
                  //   .attr("class", "slt-ego-node")
                  //   .attr('fill', function (d) {
                  //     let idx = this_.$store.getters.getselectedEgoList.indexOf(selectedEgoId);
                  //     return this_.$store.getters.getcolorSchemeList[idx];
                  //     // return this_.$store.getters.getcolorSchemeList[counterNumForR];
                  //   });                      
            })
          .catch((error) => {           
            console.error(error);
          });
      },
      ToggleEgoLevel(){
        let this_ = this;
        d3.select("#egonetseq-level-icon").on("click", function (){
           this_.$store.commit("clearegoNetSequenceRt");
           d3.selectAll("#svg-dyegonet #gcompLines > *").remove();
           d3.selectAll(".actor-track line").remove();
           this_.egonetLevel1 = !this_.egonetLevel1;           
           if(this_.$store.getters.getselectedEgoList.length > 0){
              // $(".actor-track path").remove();
              $(".links").remove();
              $(".nodes").remove();
              for(let i=0; i < this_.$store.getters.getselectedEgoList.length; i++){
                let selectedEgoId = this_.$store.getters.getselectedEgoList[i];
                this_.reRenderDyEgonet(selectedEgoId);
              }
           }
           // console.log("egonetseq-level-icon compareLineDraw out");
           // if(this_.$store.getters.getselectedEgoList.length > 1){
           //   // console.log("egonetseq-level-icon compareLineDraw in");
           //   this_.compareLineDraw();
           // }
        });
        d3.select("#egonetseq-layout-icon").on("click", function(){
          d3.selectAll("#svg-dyegonet #gcompLines > *").remove();
          this_.$store.commit("clearegoNetSequenceRt");
          this_.layoutMethodFlag = !this_.layoutMethodFlag;
          if(this_.layoutMethodFlag){
            this_.layoutMethod = "SmallMultiple";
          }else{
            this_.layoutMethod = "noname";
          }
          if(this_.$store.getters.getselectedEgoList.length > 0){
              $(".actor-track line").remove();
              $(".links").remove();
              $(".nodes").remove();
              for(let i=0; i < this_.$store.getters.getselectedEgoList.length; i++){
                let selectedEgoId = this_.$store.getters.getselectedEgoList[i];
                this_.reRenderDyEgonet(selectedEgoId);
              }
           }
           // if(this_.$store.getters.getselectedEgoList.length > 1){
           //   this_.compareLineDraw();
           // }
        });
      },
      tooltipForEgoSeq(){
          let this_ = this;
          $$(".egonetseq-level-box").jBox("Mouse", { ///
              theme: 'TooltipDark',
              content: 'Toggle showing 1-level only',
              position: {
                x: 'left',
                y: 'bottom'
             }
          });
          $$(".egonetseq-legend-box").jBox("Mouse", { ///
              theme: 'TooltipDark',
              content: 'See legend',
              position: {
                x: 'left',
                y: 'bottom'
             }
          });
          $$(".egonetseq-layout-box").jBox("Mouse", { ///
              theme: 'TooltipDark',
              content: 'Layout settings',
              position: {
                x: 'left',
                y: 'bottom'
             }
          });
      },
      callbackMouseOver(node, mouseState){ //鼠标悬浮时的回调函数. node:鼠标悬浮时的节点对象.node={id:x,name:x,position:x, value:x}.
        let this_ = this;
        let circleClass = "dyegovis-" + node.id.replace(/\./g, "-");              
        if(mouseState == "mouseover"){ //鼠标悬浮, 概览视图中的对应节点颜色高亮.
          d3.select("#ego-overview-box circle." + circleClass).attr("fill", this_.$store.getters.getcolorMap.egoColor); // overview视图中的对应的节点颜色高亮.
          d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-" + node.id.replace(/\./g, "-")).attr("fill", this_.$store.getters.getcolorMap.egoColor);
        }
        // if(mouseState == "mouseout"){ //鼠标离开, 恢复原来的颜色.
        //   // 颜色映射START
        //   let val2Color = null;
        //   console.log("xxxxxxxx node"); console.log(node);
        //   if(this_.$store.getters.getattrRadio == "position"){
        //     // val2Color = this_.$store.getters.getcolorMap.pointColorObj;
        //     val2Color = this_.$store.getters.getcolorMap.pointColorShObj[this_.$store.getters.getcolorRadio];
        //   }else{
        //     let minMaxVal = this_.$store.getters.getfilterObj[this_.$store.getters.getattrRadio]; // [min, max]
        //     let colorList = this_.$store.getters.getcolorSchemeObj[this_.$store.getters.getcolorRadio];
        //     let colorScheme = [colorList[0], colorList[colorList.length - 1]];        
        //     val2Color = d3.scaleLinear().domain(minMaxVal)
        //                       .range(colorScheme);
        //   }        
        //   // 颜色映射END
        //   if(this_.$store.getters.getselectedDataset == "enron"){
        //     d3.select("#ego-nodeoverview-box circle." + circleClass).attr("fill", function(){
        //       let attrVal = node.egoattrs[this_.$store.getters.getattrRadio]; 
        //       if(this_.$store.getters.getattrRadio == "position"){                                    
        //         return val2Color[attrVal]; 
        //       }else{ 
        //         // console.log("mouseout val2Color"); console.log(val2Color);                                                           
        //         return val2Color(attrVal);
        //       }
        //     }); // fixme: 中期时加的 
        //     d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-" + node.id.replace(/\./g, "-")).attr("fill", function(){
        //       let attrVal = node.egoattrs[this_.$store.getters.getattrRadio]; 
        //       if(this_.$store.getters.getattrRadio == "position"){                                    
        //         return val2Color[attrVal]; 
        //       }else{ 
        //         // console.log("mouseout val2Color"); console.log(val2Color);                                                           
        //         return val2Color(attrVal);
        //       }
        //     });  
        //   }
        //   if(this_.$store.getters.getselectedDataset == "tvcg"){
        //     d3.select("#ego-overview-box circle." + circleClass).attr("fill", function(){
        //       let attrVal = node.egoattrs[this_.$store.getters.getattrRadio];
        //                   return val2Color(attrVal);
        //     }); // fixme: 中期时加的 
        //     d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-" + node.id.replace(/\./g, "-")).attr("fill", function(){

        //     }); 
        //   }
        // }
      },
      debounce(func, delay){
        let timeout=null;
        return function() {        
            if(timeout) clearTimeout(timeout);
            let context = this, args = arguments;       
            timeout = setTimeout(function(){          
              func.apply(context, args);
            },delay);
        };
      },
      scrollOperate(e){
          let this_ = this;          
          $("#egonets-time-step-box").scrollLeft(e.srcElement.scrollLeft);                 
          $("#show-egonet-seq").scrollLeft(e.srcElement.scrollLeft); // div同步横向滚动条
          let adjustPos = this_.debounce(function(){            
            for(let idx = 0; idx < this_.$store.getters.getmarkRectTextList.length; idx++){
              let rectText = this_.$store.getters.getmarkRectTextList[idx]; // [rect, text]              
              let timeStepNum = Math.round(e.srcElement.scrollLeft / this_.$store.getters.gettimeStepEgonetW);             
              rectText[0]._groups[0][0].attributes[0].nodeValue = timeStepNum * this_.$store.getters.gettimeStepEgonetW;
              let X = timeStepNum * this_.$store.getters.gettimeStepEgonetW + 12; // .toString()
              rectText[1]._groups[0][0].attributes[1].nodeValue = "translate(" + X + "," + rectText[1]._groups[0][0].attributes[1].nodeValue.split(",")[1];
              // console.log("adjustPos");
            }
          }, 1000);
          adjustPos();          
      },            
      drawTimeLine(){ // 绘制时间轴.
        let this_ = this;
        d3.select("#svg-time-line *").remove(); // 清除svg中旧的内容.        
        let dateStringArray = null;
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
        // console.log("dateStringArray");console.log(dateStringArray);      
        let flowViewSvgWidth = dateStringArray.length * this_.$store.getters.gettimeStepEgonetW + this_.margin.left;
        let svg = d3.select("#svg-time-line")
          .append("g")
          .attr("id", "timeline-g")
          .attr("transform", "translate(" + (this_.$store.getters.gettimeStepEgonetW / 2 + this_.margin.left) + "," + (this_.margin.top - 2) + ")");                      
        
        let lineCircleG = svg.append("g")
                       .attr("id", "g-line-circle")
                       .attr("transform", "translate(0, 10)"); 
        let lineG = lineCircleG.append("g")
                       .attr("id", "g-line");
                       
        lineG.append("line")
          .attr("x1", 0)
          .attr("y1", 0)         
          .attr("x2", (dateStringArray.length - 1)* this_.$store.getters.gettimeStepEgonetW)
          .attr("y2", 0)
          .style("stroke", "#d3d3d3"); // #d3d3d3
        
        let circleG = lineCircleG.append("g")
                       .attr("id", "g-circle");                       
        circleG.selectAll("circle")
            .data(dateStringArray)
            .enter()
            .append("circle")            
            .attr("cx", function(d, i) { return i * this_.$store.getters.gettimeStepEgonetW; })
            .attr("cy", 0)
            .attr("r", 5)
            .style("fill", "white")
            .style("stroke", "#d3d3d3");

        // create text
        let textG = svg.append("g")
                       .attr("id", "g-text");
        let dateGroup = textG.selectAll(".date")
          .data(dateStringArray)
          .enter()
          .append("text")
          .attr("class", "date")
          .attr("transform", function(d, i) {
            return "translate(" + (i * this_.$store.getters.gettimeStepEgonetW) + ", 0)" + " rotate(0)";
          })
          .style("fill", "#090808") // 
          // .style("font", "11px sans-serif")
          .style("alignment-baseline", "middle")
          .text(function(d) {
            return d;
          });
     },
     updateTimestepNum(){
      let this_ = this;
      if(this_.$store.getters.gettimeStepSlice.length > 0){
        let startIndex = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);
        let endIndex = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[1]);
        this_.selectedTimestepNum = endIndex - startIndex + 1;
      }
      else{
        this_.selectedTimestepNum = this_.$store.getters.gettimeStepList.length;
      }
     },
     showEgoNetSeq(){
      let this_ = this;     
      let svgEgonet = d3.select("#svg-dyegonet");
      svgEgonet.append("rect").attr("id", "svg-dyegonet-bg")
                              .attr("x", 0)
                              .attr("y", 0)
                              .attr("width", this_.svgWidth)
                              .attr("height", this_.$store.getters.getselectedEgoList.length * this_.$store.getters.gettimeStepEgonetH)
                              .style("fill", "white")
                              .style("opacity", 0);
      svgEgonet.append("g").attr("id", "gcompLines")
                             .attr("transform", "translate(" + this_.margin.left + "," + this_.margin.top + ")");
      svgEgonet.append("g").attr("id", "all-dyegonets")
                           .attr("transform", "translate(" + this_.margin.left + "," + this_.margin.top + ")");
      // allDyEgonets.append("g").attr("id", "gcompLines");
     },
     createRightClickEvent(){
        let this_ = this;
        $.contextMenu({ 
          // fixme: contextMenu插件是一个事件类型的,也就是说,mounted阶段并没有'each-dyegonet-bg'这个元素,需要点击ego后才能渲染出来,但是由于这是一个事件,则直接在mounted里面注册,一旦出现这样的元素则会直接绑定到上面,在这些元素上右键点击触发对应事件.
            selector: '.each-dyegonet-bg', // 绑定的元素,当在该元素右键时,就会弹出右键选择项目. 验证去掉背景矩形.
            // selector: '.each-dyegonet', // 绑定的元素,当在该元素右键时,就会弹出右键选择项目.
            className: "dyegonetContextMenu",
            callback: function(key, options) {
               // console.log("options callback callback"); console.log(options);              
               if(key == "delete"){  // 如果点击的是"delete"选项.               
                 let curDyegonetId = options.$trigger["0"].parentElement.id; // 当前右键删除的dyegonet的id. 
                 let curOrder = parseInt(curDyegonetId.split("-")[1]);
                 $("#dyegonet-" + curOrder).remove(); //删除该行.
                 // d3.selectAll("#svg-dyegonet #gcompLines line").remove();
                 d3.selectAll("#svg-dyegonet #gcompLines > *").remove();
                 let dyegonetLen = this_.$store.getters.getselectedEgoList.length;
                 this_.$store.commit("removeOneselectedEgoList", curOrder); // 删除store.js中selectedEgoList中索引为curOrder的元素,即删除行对应的ego.
                 // todo: 现在的问题: 更改selectedEgoList会被监听. 解决方案: 使用bus事件替代监听.
                 for(let i = curOrder + 1; i < dyegonetLen; i++){
                    // console.log("jj");console.log(i);
                    d3.select("#dyegonet-" + i).attr("id", "dyegonet-" + (i - 1)) // 更改g的id.
                                               .attr("transform", "translate(0, " + (this_.$store.getters.gettimeStepEgonetH + this_.marginDyEgonet)* (i - 1) + ")"); // 位置上移一行.
                    d3.select(".eachdyegonetbg-" + i).attr("class", "each-dyegonet-bg eachdyegonetbg-" + (i - 1)); // 更改rect元素的类名. 验证去掉背景矩形.
                 }
                 // 去掉概览中节点被点击后的高亮
                 let egoId = options.$trigger["0"].parentElement.attributes[2].value;                 
                 delete this_.clickActorSet[egoId]; // 修改后
                 let newEgoId = egoId.replace(/\./g, "-");
                 let overviewEgoId = "dyegovis-" + newEgoId;
                 d3.select("#ego-overview-box circle." + overviewEgoId)
                   .attr("stroke", "#d1d1d1")
                   .attr("stroke-width", 1); //attr("stroke-width", 0);
                 d3.selectAll("#search-result-box tr.row-" + overviewEgoId + ">td").attr("style", "background-color: #0000"); // row的高亮取消
                 /*remove all track lines*/
                 d3.select(".tracklineg-" + newEgoId).remove();          
                 let index = this_.$store.getters.getclickedEgoList.indexOf(egoId);            
                 this_.$store.commit("removeOneclickedEgoList", index);
                 // 用于颜色编码
                 this_.$store.commit("removeOneegoNetSequenceRt", index);           
                 d3.selectAll(".overview-" + newEgoId)
                    .attr("stroke", "#d1d1d1")
                    .attr("stroke-width", 1); // 节点边缘颜色为黑色.
                 if(this_.$store.getters.getselectedEgoList.length > 1){
                   this_.compareLineDraw();
                 }
                 this_.$store.commit("removeOneselectedEgoObj", egoId);
                 // this_.markRectTextList.splice(index, 1); // 删除对应的元素.
                 this_.$store.commit("removeOnemarkRectTextList", index);                
                 d3.select("#ego-overview-box text." + overviewEgoId).attr("display", "none"); // 不显示标签.
                 // let curTimeStep = 
                 d3.selectAll("#svg-egonets-time-step .overview-points text." + "txviewg-" + egoId.replace(/\./g, "-")).attr("display", "none");
               }
               if(key == "copy"){                          
                 d3.selectAll(".each-dyegonet").remove(); //删除该行.
                 // d3.selectAll("#svg-dyegonet #gcompLines line").remove(); 
                 d3.selectAll("#svg-dyegonet #gcompLines > *").remove();              
                 for(let key in this_.clickActorSet){ // 清空对象.
                    delete this_.clickActorSet[key];
                 }
                 for(let i = 0; i < this_.$store.getters.getselectedEgoList.length; i++){
                  d3.select("#ego-overview-box text.dyegovis-" + this_.$store.getters.getselectedEgoList[i].replace(/\./g, "-")).attr("display", "none"); // 不显示标签.
                  d3.selectAll("#svg-egonets-time-step .overview-points text." + "txviewg-" + this_.$store.getters.getselectedEgoList[i].replace(/\./g, "-")).attr("display", "none");
                 }
                 this_.$store.commit("clearselectedEgoList"); // 清除选中的ego节点.
                 d3.selectAll("#ego-overview-box .point circle").attr("stroke", "#d1d1d1").attr("stroke-width", 1); //先消除所有的高亮.                 
                 d3.selectAll("#track-lines-g g").remove();          
                 for(let i = 0; i < this_.$store.getters.getclickedEgoList.length; i++){                                    
                  d3.selectAll(".overview-" + this_.$store.getters.getclickedEgoList[i].replace(/\./g, "-"))
                    .attr("stroke", "#d1d1d1")
                    .attr("stroke-width", 1); // "dyegovis-"
                  // console.log("jjjjjjjjjjj copy for");
                  // d3.select("#ego-overview-box text.dyegovis-" + this_.$store.getters.getclickedEgoList[i].replace(/\./g, "-")).attr("display", "none"); // 不显示标签.
                  // d3.selectAll("#svg-egonets-time-step .overview-points text." + "txviewg-" + this_.$store.getters.getclickedEgoList[i].replace(/\./g, "-")).attr("display", "none");
                }                
                this_.$store.commit("clearclickedEgoList");       
                // if(this_.$store.getters.getselectedEgoList.length > 1){
                //   this_.compareLineDraw();
                // }
                this_.$store.commit("clearAllselectedEgoObj"); // 清除所有.
                this_.$store.commit("clearegoNetSequenceRt");
                // this_.markRectTextList.splice(0, this_.markRectTextList.length); // 
                this_.$store.commit("clearmarkRectTextList");    
              }
            },
            items: {
                "delete": {name: "Delete it"},
                "copy": {name: "Delete all"},
                "quit": {name: "Quit"}
            },
            zIndex: 1200
        });

     }
    },
    created(){
      let this_ = this;
      bus.$on("selectDynamicEgonet", function(egoIdName){ // 就是真实的ego的ID egoIdName=[egoId, egoName]
        let selectedEgoId = egoIdName[0];
        if(selectedEgoId){ // ego的id.          
          let curVal = this_.$store.getters.getselectedEgoList; // 获取已经选中的ego列表          
          let svgH = curVal.length * (this_.$store.getters.gettimeStepEgonetH + this_.marginDyEgonet);          
          d3.select("#svg-dyegonet").attr("height", svgH); // 更改svg的高
          d3.select("#svg-dyegonet-bg").attr("height", svgH); // 更改svg背景的高
          let gEgonetX = 0;
          let gEgonetY = (this_.$store.getters.gettimeStepEgonetH + this_.marginDyEgonet)* (curVal.length - 1); // 管理元素g的位置.
          /*
           首先,确定绘制行, 例如<g class="each-dyegonet" id="dyegonet-0" name="joe.stepenovitch">,
           然后在该行中划分时间步, 例如<g class="egonet-at-timestep egonet-0" name="2000-03">).
          */
          // fixme: 首先绘制 行 + 时间步格子.
          let selectedDyEgoNet = d3.select("#all-dyegonets").append("g") //添加一行用于展示当前选中的dyegonet.
                                              .attr("class", "each-dyegonet")
                                              .attr("id", "dyegonet-" + (curVal.length - 1))
                                              .attr("name", selectedEgoId) //curVal[curVal.length - 1]) // ego的ID, 对于安然数据是人的名称.
                                              .attr("transform", "translate(" + gEgonetX + "," + gEgonetY + ")");
          selectedDyEgoNet.append("rect") // 添加背景,用于确定绘制图的大小,以及边框样式设计.
                          .attr("class", "each-dyegonet-bg " + "eachdyegonetbg-" + (curVal.length - 1))
                          .attr("width", this_.$store.getters.gettimeStepEgonetW * this_.selectedTimestepNum)
                          // .attr("height", this_.$store.getters.gettimeStepEgonetH + this_.nodeNameText)
                          .attr("height", this_.$store.getters.gettimeStepEgonetH)
                          .attr("x", 0)
                          .attr("y", 0)
                          .style("fill", "white")                          
                          .style("opacity", 0); // 验证去掉背景矩形.
          let egoMarkRect = selectedDyEgoNet.append("rect")
                          .attr("x", 0)
                          .attr("y", this_.$store.getters.gettimeStepEgonetH + this_.nodeNameText - 9)
                          .attr("width", 10)
                          .attr("height", 10)
                          .attr("class", "ego-lgd-mk")                          
                          .attr("fill", function (){
                            // selectedEgoId
                            let egoIdx = this_.$store.getters.getselectedEgoList.indexOf(selectedEgoId);
                            return this_.$store.getters.getcolorSchemeList[egoIdx];
                          });
          let egoNameText = selectedDyEgoNet.append("text")
                          .attr("class", "slct-ego text-" + selectedEgoId.replace(/\./g, "-"))
                          .attr("transform", "translate(12" + "," + (this_.$store.getters.gettimeStepEgonetH + this_.nodeNameText) + ")")
                          .text(function(){
                            let tempObj = {};
                            tempObj[egoIdName[0]] = egoIdName[1]; // {ego: name:xxx}
                            this_.$store.commit("addOneForselectedEgoObj", tempObj);
                            return egoIdName[1];
                          });
          // this_.markRectTextList.push();
          this_.$store.commit("addOnemarkRectTextList", [egoMarkRect, egoNameText])
          selectedDyEgoNet.append("g")
                          .attr("class", "actor-track");                                                                  
          let startIndex = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]); // 起始时间的索引.         
          for(let i=0; i<this_.selectedTimestepNum; i++){ // 根据时间步数,添加对应的格子,用于绘制egonet. 

            let timestepX = this_.$store.getters.gettimeStepEgonetW * i;
            let eachTimestepG = selectedDyEgoNet.append("g")
                                                .attr("class", "egonet-at-timestep" + " egonet-" + i)                                                
                                                .attr("name", this_.$store.getters.gettimeStepList[startIndex + i]) // name="2001"
                                                .attr("transform", "translate(" +  timestepX + ",0)");
            
            eachTimestepG.append("rect") // 添加snapshot的背景,用于确定绘制图的大小,以及边框样式设计.
                          .attr("class", "egonet-bg")
                          .attr("width", this_.$store.getters.gettimeStepEgonetW)
                          .attr("height", this_.$store.getters.gettimeStepEgonetH)
                          .attr("x", 0)
                          .attr("y", 0)
                          .style("fill", "none")
                          .style("stroke", "#aaa") // 背景颜色#aaa
                          .style("opacity", 0.5);
            
          }          
          // fixme: 绘制行 + 时间步格子后,将每个时间步对应的egonet绘制到相应的格子中.
          let timeInterval = this_.$store.getters.gettimeStepSlice; // [2000-02, 2002-01]
          let timeStepList = this_.$store.getters.gettimeStepList; // [x, x, ...]
          if(timeStepList[0] == timeInterval[0] && timeStepList[timeStepList.length - 1] == timeInterval[1]){
             timeInterval = []; // 代表整个时间轴.
          }
          let param = {dbname: this_.$store.getters.getselectedDataset, timeInterval: timeInterval, ego: selectedEgoId, egonetLevel1: this_.egonetLevel1}; // ego: curVal[curVal.length - 1]
          /*
            说明: 当用户点击一个节点时, 先在svg中绘制一行, 然后在这一行中根据时间步数绘制格子,最后拿着id向后台请求对应的egonet, 响应后, 先找到对应的行, 然后找到对应的格子并将egonet布局在格子中.
          */
          axios.post(vueFlaskRouterConfig.selecteddyegonet, { // 请求ego对应的序列.
             param: JSON.stringify(param)
          })
          .then((res) => {
                  // console.log("click ego respond data"); console.log(res.data);
                  let graph = res.data.dyegonet; // egonet序列. 
                  let nbrs1t = res.data.nbrs1t;
                  let nbrs1MaxSize = res.data.maxs1; // 当前序列的最大egonet的节点数量
                  let egots = res.data.egots; // [startTime, endTime] 
                  let posNumAlter1 = res.data.pos_num_alter1;
                  let posNumAlter2 = res.data.pos_num_alter2;
                  let nbrs12List = res.data.nbrs12; 
                  let nbrs12t = res.data.nbrs12t; // {id1: [1, 2, 4, 6], ...}, 每个alter12出现的时间步.          
                  /*res.data:
                    {
                      dyegonet: {2000-03: {nodes: {ego: {id:x, name:x, ...}, nbrs1: [{}, ...], nbrs2: [{}, ...]}, links: {nbrs1: [{source: x, target: x, weight: x}, ...], nbrs2: [{}, ...]}}, ...},
                      nbrs1t: {pos: {a1: [-1, -2, -1], ...}, tslice: {a1: [4, 6], ...}}, // 1-level邻居的布局位置(pos), 以及起始和终止时间(tslice).
                      nbrs2t: {pos: {b1: [-1, -2, -1], ...}, tslice: {b1: [4, 6], ...}} // 2-level邻居的布局位置(pos), 以及起始和终止时间(tslice).
                      maxs1: x, // alter1偏离ego的最大位置
                      maxs2: x, // alter2偏离ego的最大位置
                      egots: [x, x] // dyegonet的时间切片, i.e., [start_time, end_time]
                      pos_num_alter1: [x, x, x, ...],
                      pos_num_alter2: [x, x, ,x, ...],
                      nbrs12: [x, ...]
                    }
                  */               
                  let svgWidth = this_.$store.getters.gettimeStepEgonetW;
                  let svgHeight = this_.$store.getters.gettimeStepEgonetH;                                  
                  let selectorP = "#svg-dyegonet #all-dyegonets .each-dyegonet[name=" + "'" + selectedEgoId + "'" +  "]" + " .egonet-at-timestep"; // 找到序列所在的行.
                  // let selectorTrackg = "#svg-dyegonet #all-dyegonets .each-dyegonet[name=" + "'" + selectedEgoId + "'" +  "]" + " .actor-track"; // 当前行所在的追踪线g.
                  let svgIdSelector = "#svg-dyegonet";
                  let selectElementName = d3.selectAll(selectorP)._groups[0]; // 时间步对应的元素: [g, g, ...]                  
                  let isDirected = false;
                  let layoutSettings = null;
                  if(this_.layoutMethod == "SmallMultiple"){
                      layoutSettings = { // 布局参数设置.
                        linkLength: 10,
                        chargeStrength: -100,
                        edgeMode: "line",
                        labelDisplay: false,
                        limitBox: true,
                        nodeColor:"#FF8700",
                        radius: 5,
                        curDataset: this_.$store.getters.getselectedDataset,
                        egoId: selectedEgoId
                      };
                  }                  
                  //add
                  let nbrs1WH = null;
                  let DPforWH = null;
                  let trackLinks = null;
                  let curRowSelector = "#svg-dyegonet #all-dyegonets .each-dyegonet[name=" + "'" + selectedEgoId + "'" + "]"; // 当前所在行
                  if(this_.layoutMethod == "noname"){
                    nbrs1WH = this_.computedetanbrs1H(nbrs1MaxSize, svgWidth, svgHeight); // 获得边与高的步进.
                    if(nbrs1WH[2]){
                      DPforWH = this_.computeBasedWHForTimeSlice(posNumAlter1, posNumAlter2, svgWidth, svgHeight); // {sliceStartIdx: [], ..., sliceEndIdx: []}
                    }
                    let linksList = this_.computenbrs1TrackLinks(nbrs1t, svgWidth, svgHeight, nbrs1WH[0], nbrs1WH[1], egots, selectedEgoId, nbrs1WH[2], DPforWH, nbrs12t, nbrs12List); // let nbrs12t = res.data.nbrs12t; // {id1: [1, 2, 4, 6], ...}, 每个alter12出现的时间步. 
                    let selectorTrackg = "#svg-dyegonet #all-dyegonets .each-dyegonet[name=" + "'" + selectedEgoId + "'" +  "]" + " .actor-track"; // 当前行所在的追踪线g.
                    trackLinks = this_.drawnbrs1TrackLinks(selectorTrackg, linksList);
                  }                  
                  // add
                  let nodecirclesList = [];
                  for(let i=0; i<selectElementName.length; i++){ // 一行中, 逐个绘制每个时间步的snapshot.
                    let eachElement = selectElementName[i];                    
                    let timeStep = eachElement.attributes[1].nodeValue; // 例如, "2000-03"                    
                    let selectedPath = "#svg-dyegonet #all-dyegonets .each-dyegonet[name=" + "'" + selectedEgoId + "'" + "]" + " .egonet-" + i;
                    if(this_.layoutMethod == "SmallMultiple"){
                      let egonetLen = graph[timeStep].nodes.nbrs1.length + graph[timeStep].nodes.nbrs2.length + 1;
                      if(egonetLen < 30){
                        layoutSettings.chargeStrength = -80;
                      }else{
                        layoutSettings.chargeStrength = -20;
                      }
                      // 颜色映射 Start
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
                      // 颜色映射 End  val2Color, this_.$store.getters.getattrRadio                 
                      let nodecircles = d3GraphLayout(graph[timeStep], isDirected, layoutSettings, selectedPath, svgWidth, svgHeight, svgIdSelector, null, null, this_.callbackMouseOver, null, val2Color, this_.$store.getters.getattrRadio, this_.$store.getters.getselectedEgoList, this_.$store.getters.getcolorSchemeList, selectedEgoId, this_.callbackMouseout); // 力导引布局展示
                      nodecirclesList.push(nodecircles);
                    }
                    if(this_.layoutMethod == "noname"){
                      let timeStepIdx = this_.$store.getters.gettimeStepList.indexOf(timeStep);
                      let sliceStartIdx = 0; // 时间区间的起始位置.          
                      if(this_.$store.getters.gettimeStepSlice.length > 0){
                        sliceStartIdx = this_.$store.getters.gettimeStepList.indexOf(this_.$store.getters.gettimeStepSlice[0]);            
                      }
                      let nbrLevel = this_.egonetLevel1 ? 1 : 2; // 当前的层数.                     
                      let nodecircles = this_.layoutEgonet(timeStepIdx, graph[timeStep], nbrs1t, nbrs1WH[0], nbrs1WH[1], selectedPath, svgWidth, svgHeight, nbrLevel, 4, trackLinks, curRowSelector, selectedEgoId, nbrs1WH[2], DPforWH, nbrs12List);
                      nodecirclesList.push(nodecircles);                    
                    }
                  }
                  // 将 nodecirclesList 添加到 addOneegoNetSequenceRt中.
                  this_.$store.commit("addOneegoNetSequenceRt", nodecirclesList); // let nodecirclesList = []; nodecircles
                  if(this_.$store.getters.getselectedEgoList.length > 1){
                    this_.compareLineDraw();
                  }
                  //找到ego节点,并更改其颜色填充.
                  let curEgo = selectedEgoId; // curVal[curVal.length - 1];
                  let newEgoId = curEgo.split("."); // [x, x, ...]
                  let nodeClassStr = "";
                  if(newEgoId.length > 1){
                    let counter = newEgoId.length;
                    for(let i=0; i<counter; i++){
                        if(i<counter-1){
                          nodeClassStr = nodeClassStr + newEgoId[i] + "-";
                        }else{
                          nodeClassStr = nodeClassStr + newEgoId[i];
                        }
                    }
                  }
                  else{
                    nodeClassStr = newEgoId[0];
                  }              
            })
          .catch((error) => {           
            console.error(error);
          });
                                        
        }
      });
    },
    mounted(){
      let this_ = this;      
      this_.showEgoNetSeq();
      this_.createRightClickEvent();
      this_.tooltipForEgoSeq();
      this_.ToggleEgoLevel();
      this_.jBoxInstance.nodeDetail = new jBox("Modal", {
            id: "jBox-nodeinfo",
            addClass: "jBox-egonetninfo",  // 添加类型,这个功能很棒啊!
            attach: '.egonetnOVContextMenu',  // 这是历史走廊的图标.点击这个图标打开历史走廊弹窗.
            maxWidth: 500,            
            maxHeight: 550,
            // adjustTracker:true,
            title: 'Node Details',
            overlay: false,
            zIndex: 1005, // fixme:注意多个jBox实例之间zIndex的值决定与最后一个实例.
            createOnInit: true,
            content: $("#overview-egonetnodes-info"),  // jQuery('#jBox-content') 
            draggable: true,
            repositionOnOpen: false,
            repositionOnContent: true,    
            target: $('#dyegonet-view'),
            offset: {x: -110, y: -60},            
            onCloseComplete: function(){               
               let pointSt = "#svg-dyegonet #all-dyegonets .each-dyegonet[name='" + this_.curClickedEgo + "']" + " .egonet-at-timestep[name='" + this_.curTimeStep + "']" + " .nodes .dyegovis-" + this_.curViewNode.replace(/\./g, "-"); // curTimeStep             
               // d3.select(pointSt).attr("stroke", "#d1d1d1").attr("stroke-width", 1); // 高亮点.                
               if(this_.clickActorSet.hasOwnProperty(this_.curClickedEgo)){
                if(this_.clickActorSet[this_.curClickedEgo].indexOf(this_.curViewNode) != -1){
                  d3.select(pointSt).attr("stroke", "#de2d26").attr("stroke-width", 1);
                  // console.log("track line restore");
                }else{
                  d3.select(pointSt).attr("stroke", "#d1d1d1").attr("stroke-width", 1);
                  // console.log("no track line restore");
                }
               }else{
                d3.select(pointSt).attr("stroke", "#d1d1d1").attr("stroke-width", 1);
               }
               this_.curViewNode = null;
               this_.curTimeStep = null; 
               this_.curClickedEgo = null;      
            }
      });
      this_.contextMenuForNode();   
    },
    updated(){
      console.log("egoNetSequences updated");
      let this_ = this;
      this_.drawTimeLine(); // 置于updated钩子函数中,使得时间轴能随着时间区间的选择而实时变化.
      // this_.createRightClickEvent();      
    },
    beforeDestroy(){
      console.log("egoNetSequences beforeDestroy");
      bus.$off("selectDynamicEgonet");
    }
  }
</script>
<style> 
  @import "../../static/css/jquery.contextMenu.css";
  /*.context-menu-list {
    position: absolute; 
    display: inline-block;
    min-width: 150px;
    max-width: 350px;
    padding: .25em 0;
    margin: .3em;
    font-family: inherit;
    font-size: inherit;
    list-style-type: none;
    background: #fff;
    border: 1px solid #bebebe;
    border-radius: .2em;  
}*/
</style>>