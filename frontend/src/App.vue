<template>
  <div id="app">   
   <!-- App.vue作为页面入口文件 -->
    <div id="system-interface-box">
     <el-row class="entire-sys" :gutter="1"> <!--system div-->
      <el-row class="head-sys" :gutter="1"> <!--header div-->
        <div id="navg-div">
          <div class="app-setting">           
             <div class="setting-box">
                <selectdataset></selectdataset>
             </div>
             <div class="setting-box time-line-setting">
                <span class="md-name">Timespan:</span>
                <timelineslice></timelineslice>
             </div> 
                       
             <!-- <div class="setting-box time-line-setting">
                <span class="md-name">Norm:</span>
                <select id="method-norm-select">
                  <option v-for="(eachOne,index) in methodNorm" :value="index">{{eachOne}}</option>               
                </select>
             </div>  -->

             <div class="setting-box time-line-setting">
                <span class="md-name">Projection:</span>
                <select id="method-rd-select">
                  <option v-for="(eachOne,index) in methodRDOption" :value="index">{{eachOne}}</option>               
                </select>
             </div>          
             
             <!-- <div v-show="$store.getters.getselectedMethodRD != 'PCA'" class="setting-box time-line-setting">
                <span class="md-name">Distance:</span>
                <select id="distance-select">
                  <option v-for="(eachOne,index) in distanceOption" :value="index">{{eachOne}}</option>               
                </select>
             </div> -->

             <div class="setting-box time-line-setting">
                <span class="md-name">Filter:</span>
                <div class="overview-filter-box" id="filter-egos-icon">
                   <img class="overview-img-icon" id="overview-filter-icon-img" width="16" height="16" src="../static/img/filter.svg">
                </div>
             </div>

             <div class="setting-box time-line-setting">
                <span class="md-name">Color-Encoder:</span>
                <div class="point-attr-map" id="colormap-icon">
                   <img id="colormap-icon-img" width="16" height="16" src="../static/img/colorMap.svg">
                </div>
             </div>

             <div class="setting-box time-line-setting">
                <span class="md-name">Refresh:</span>
                <timelineslicerefresh></timelineslicerefresh>
             </div>
             <div class="setting-box time-line-setting">
               <span class="md-name">Legend:</span>
               <div id="legend-div-bx">
                <img id="lgd-icon-img" width="17" height="17" src="../static/img/legend.svg">              
               </div>
             </div>
             <div class="setting-box time-line-setting">
               <searchbox></searchbox>
             </div>
          </div>
          <div id="us-help">
             <div class="rt-text">About Us</div>
             <!-- <div class="rt-text">Help</div> -->
          </div>
        </div>        
      </el-row>
      <el-row class="body-sys" :gutter="1"> <!--body div-->        
        <splitpanes watch-slots @resized="listenResized('resized', $event)" class="default-theme"> <!-- watch-slots 使用resize组件-->
          <pane :maxSize="leftBoxSplitSize" class="left-div"> <!--left div-->
            <div id="egooverview">
              <egooverview></egooverview>
            </div>
            <div id="timecurveview">
              <timecurveview></timecurveview>
            </div>
          </pane>        
          <pane :minSize="rightBoxSplitSize" class="right-div"> <!--left div-->                 
            <egonetsequences></egonetsequences>
          </pane>
        </splitpanes>
      </el-row>       
     </el-row>
    </div>
    <div id="overview-for-filter">    
      <div v-if="key != 'total_p_num'" class="filter-item" v-for="(value,key) in $store.state.App.filterObj">
        <span v-if="key != 'avg_tie'" class="feature-name">{{key}}:</span>
        <span v-else class="feature-name">avg_weight:</span>
        <el-slider range v-model="filterIterms[key]" :min="0" :max="value[1]" :step=0.1></el-slider>            
      </div>
      <div v-else class="filter-item">
        <span class="feature-name">{{key}}:</span>
        <el-slider range v-model="filterIterms[key]" :min="0" :max="value[1]" :step=1></el-slider>            
      </div>
      <div id="check-filterinfo">
        <div id="filter-ok">          
          OK
        </div>
      </div>     
    </div> 
    <div id="map-attr-color">
      <div class="color-mpdv" id="select-arr">
         <div class="cl-dscp"><span>Select an attribute:</span></div>
         <div>
           <el-radio-group v-model="$store.state.App.attrRadio">
            <el-radio v-if="value != 'avg_tie'" :label="value" v-for="(value,index) in $store.getters.getgetCandidateAttrs">{{value}}</el-radio>
            <el-radio v-else :label="value" >avg_weight</el-radio>          
           </el-radio-group>
         </div>
      </div>
      
      <div class="color-mpdv" id="select-color">
        <div class="cl-dscp"><span>Select a color scheme:</span></div>
        <div>
           <el-radio-group v-model="$store.state.App.colorRadio">
            <el-radio :label="key" v-for="(colorList,key) in $store.getters.getcolorSchemeObj">
              <svg :width="unitColorW * colorList.length" :height="unitColorH">
                <rect :width="unitColorW" :height="unitColorH" :x="unitColorW * idx" y="0" :fill="color" v-for="(color, idx) in colorList"></rect>
              </svg>
            </el-radio>          
           </el-radio-group>
        </div>
      </div>
      <div id="check-cmpinfo">
        <div id="cmp-ok">          
          OK
        </div>
      </div>
    </div>
    <div id="overviews-for-legend">      
    </div>
    <stackedgraph></stackedgraph>
  </div>
</template>

<script>
  // eslint-disable-next-line
  /* eslint-disable */
  import Vue from 'vue' 
  import * as d3 from '../static/js/d3.v4.min.js' 
  import bus from './eventbus.js' // 事件总线.  
  import {vueFlaskRouterConfig} from './flaskRouter'
  import * as $ from "../static/js/jquery.min.js"  
  import axios from 'axios'
  import qs from 'qs'
  import {Splitpanes, Pane} from 'splitpanes' // splitter/resizer
  // import 'splitpanes/dist/splitpanes.css'
  import selectdataset from '@/components/selectDataset'
  import egooverview from '@/components/egoOverview'
  import timelineslice from '@/components/timeLineSlice'
  import timelineslicerefresh from '@/components/timeLineSliceRefresh'
  import egonetsequences from '@/components/egoNetSequences'
  import timecurveview from "@/components/timeCurveView"
  import stackedgraph from "@/components/stackedGraph"
  import searchbox from "@/components/searchBox"
  import {jBox} from "../static/js/jBox.js"
  //egoOverviewTimeStep
  // import egooverviewtimestep from "@/components/egoOverviewTimeStep"
  axios.interceptors.request.use(function (config) { // 只在App.vue中设置axios.interceptors.request.use就可以了,这样可避免跨域问题.切记:在flask中要用methods=["POST", "GET"],否则会出错的.
    if (config.method == 'post') {
      config.data = qs.stringify(config.data)
    }
    return config;
  }, function (error) {
    return Promise.reject(error);
  });

  export default {
    name: 'App',
    data(){
      return {        
       // distanceOption: ["Canberra Distance", "Euclidean Distance"],
       methodRDOption: ["PCA", "MDS", "t-SNE"], // "CMDS" 原来, ["MDS", "t-SNE", "PCA"]
       // methodNorm: ["Z-Score", "Min-Max", "None"], // 原来, ["None", "Min-Max", "Z-Score"],
       leftBoxSplitSize: 29,
       rightBoxSplitSize: 71,
       jBoxInstance: {
          filter: null,
          colorEncode: null,
          legend: null
       },
       // ["avg_alter_num", "avg_density", "avg_tie", "avg_alterE_num", "avg_alter2_num", "avg_alter_alters", total_p_num]
       filterIterms: {
         avg_alter_num: [0, 0],
         avg_density: [0, 0],
         avg_tie: [0, 0],
         avg_alterE_num: [0, 0],
         avg_alter2_num: [0, 0],
         avg_alter_alters: [0, 0],
         total_p_num: [0, 0]
       },            
       unitColorW: 4,
       unitColorH: 10,
       ldColorW: 35, 
       ldColorH: 15, // ["unknown", "Employee", "Trader", "In House Lawyer", "Manager", "Managing Director", "Director", "Vice President", "President", "CEO"]
       positionList: ["Unknown", "Employee", "Trader", "Lawyer", "Manager", "MD", "Director", "VP", "President", "CEO"]
      }
    },
    created(){ 
      let this_ = this;     
      console.log("App.vue created");
      // datasetList
      let path = vueFlaskRouterConfig.dbnames;
      axios.get(path) // 用get的速度大于用post.
      .then((res) => {                        
          let data = res.data; // 获得指定数据库表格中的字段.            
          let dbnamelist = data.dbnamelist; // data = {dbnamelist: [x, ...]}        
          this_.$store.commit("changedatasetList", dbnamelist);
        })
      .catch((error) => {            
        console.error(error);
      }); 
           
    },
    methods: { 
      changeColorMap(selectedAttr, colorScheme, colorRadio){ // 更改颜色所编码的属性.
        /*
          selectedAttr: x, 选中的被编码属性, colorScheme: [startColor, endColor], 颜色编码方案.
        */  
        // console.log("this_.$store.getters.getcolorRadio"); console.log(this_.$store.getters.getcolorRadio);  // this_.$store.state.colorRadio    
        let this_ = this;
        if(!selectedAttr){
          return;
        }
        if(selectedAttr == "position"){
          // dyegonet embedding view this_.$store.getters.getcolorMap.pointColorShObj[this_.$store.getters.getcolorRadio]
          let whichSch = this_.$store.getters.getcolorRadio;
          // console.log("this_.$store.getters.getcolorRadio"); console.log(this_.$store.getters.getcolorRadio);
          let dyEgoOVRt = this_.$store.getters.getegoOverviewRt;
          let nodegList = dyEgoOVRt._groups[0];          
          for(let i=0; i<nodegList.length; i++){
            let curg = nodegList[i];            
            let attrVal = curg.__data__.egoattrs[selectedAttr];            
            curg.childNodes[0].attributes[3].nodeValue = this_.$store.getters.getcolorMap.pointColorShObj[whichSch][attrVal]; //         
          }
          // egonet embedding view
          let egoSnapshotOVRt = this_.$store.getters.getegoOverviewTimeStepRt; // [ut, tu, ...]
          // console.log("changeColorMap egoSnapshotOVRt"); console.log(egoSnapshotOVRt);
          for(let ii=0; ii<egoSnapshotOVRt.length; ii++){
            let overViewObj = egoSnapshotOVRt[ii];
            let nodegList = overViewObj._groups[0];
            for(let i=0; i<nodegList.length; i++){
              let curg = nodegList[i];
              // enron: avg_tie, avg_alter_num, position; tvcg: total_p_num, avg_alter_num, avg_tie
              let attrVal = curg.__data__.egoattrs[selectedAttr];
              // console.log("changeColorMap attrVal"); console.log(attrVal);
              curg.childNodes[0].attributes[3].nodeValue = this_.$store.getters.getcolorMap.pointColorShObj[whichSch][attrVal];         
            }
          }
          // dyegonet view
          let dyegonetRt = this_.$store.getters.getegoNetSequenceRt; // [[ut, ut, ...], [ut, ut, ...], ...]
          // console.log("changeColorMap dyegonetRt"); console.log(dyegonetRt);
          for(let iii=0; iii<dyegonetRt.length; iii++){
            let dyegonetList = dyegonetRt[iii]; // [ut, ut, ...]
            for(let ii=0; ii<dyegonetList.length; ii++){
              let overViewObj = dyegonetList[ii]; // ut
              let nodegList = overViewObj._groups[0]; // [circle, ...]
              for(let i=0; i<nodegList.length; i++){
                let curg = nodegList[i]; // circle
                // enron: avg_tie, avg_alter_num, position; tvcg: total_p_num, avg_alter_num, avg_tie
                let attrVal = curg.__data__[selectedAttr];
                // console.log("changeColorMap attrVal"); console.log(attrVal);
                curg.attributes[4].nodeValue = this_.$store.getters.getcolorMap.pointColorShObj[whichSch][attrVal];         
              } 
            }
          }
        }else{
          // this_.filterObj: {f1: [min, max], ...}
          let minMaxVal = this_.$store.getters.getfilterObj[selectedAttr]; // [min, max]          
          var val2Color = d3.scaleLinear().domain(minMaxVal)
                            .range(colorScheme);        
          let dyEgoOVRt = this_.$store.getters.getegoOverviewRt;
          let nodegList = dyEgoOVRt._groups[0];
          for(let i=0; i<nodegList.length; i++){
            let curg = nodegList[i];
            // enron: avg_tie, avg_alter_num, position; tvcg: total_p_num, avg_alter_num, avg_tie
            let attrVal = curg.__data__.egoattrs[selectedAttr];
            // console.log("changeColorMap attrVal"); console.log(attrVal);
            curg.childNodes[0].attributes[3].nodeValue = val2Color(attrVal);           
          }
          // egonet embedding view
          let egoSnapshotOVRt = this_.$store.getters.getegoOverviewTimeStepRt; // [ut, tu, ...]
          // console.log("changeColorMap egoSnapshotOVRt"); console.log(egoSnapshotOVRt);
          for(let ii=0; ii<egoSnapshotOVRt.length; ii++){
            let overViewObj = egoSnapshotOVRt[ii];
            let nodegList = overViewObj._groups[0];
            for(let i=0; i<nodegList.length; i++){
              let curg = nodegList[i];
              // enron: avg_tie, avg_alter_num, position; tvcg: total_p_num, avg_alter_num, avg_tie
              let attrVal = curg.__data__.egoattrs[selectedAttr];
              // console.log("changeColorMap attrVal"); console.log(attrVal);
              curg.childNodes[0].attributes[3].nodeValue = val2Color(attrVal);           
            }
          }
          // dyegonet view
          let dyegonetRt = this_.$store.getters.getegoNetSequenceRt; // [[ut, ut, ...], [ut, ut, ...], ...]
          // console.log("changeColorMap dyegonetRt"); console.log(dyegonetRt);
          for(let iii=0; iii<dyegonetRt.length; iii++){
            let dyegonetList = dyegonetRt[iii]; // [ut, ut, ...]
            for(let ii=0; ii<dyegonetList.length; ii++){
              let overViewObj = dyegonetList[ii]; // ut
              let nodegList = overViewObj._groups[0]; // [circle, ...]
              for(let i=0; i<nodegList.length; i++){
                let curg = nodegList[i]; // circle
                // enron: avg_tie, avg_alter_num, position; tvcg: total_p_num, avg_alter_num, avg_tie
                let attrVal = curg.__data__[selectedAttr];
                // console.log("changeColorMap attrVal"); console.log(attrVal);
                curg.attributes[4].nodeValue = val2Color(attrVal);         
              } 
            }
          }
        }
      },     
      filterEvent(){ // 定义点击过滤图标时的事件.
        let this_ = this;
        bus.$on("getobj4Filter", function(obj4Filter){
          // this_.filterObj = obj4Filter;
          this_.$store.commit("changefilterObj", obj4Filter);
          // if(this_.$store.getters.getselectedDataset == "enron"){
          //   // this_.attrRadio = "position";
          //   this_.$store.commit("changeattrRadio", "position");
          // }
          // if(this_.$store.getters.getselectedDataset == "tvcg"){
          //   // this_.attrRadio = "total_p_num";
          //   this_.$store.commit("changeattrRadio", "total_p_num");
          // }          
          // this_.$store.commit("changegetFilterInfoFlag", true);
          for(let ft in this_.$store.getters.getfilterObj){ // this_.filterObj: {f1: [min, max], ...}
            this_.filterIterms[ft] = [this_.$store.getters.getfilterObj[ft][0], this_.$store.getters.getfilterObj[ft][1]]; // 更新最大最小范围.                  
          }
          this_.$store.commit("changefilterIterms", this_.filterIterms); // 初始化store.js中的filterIterms.
        });        
      },
      mouseEvents(){
        let this_ = this;
        $(".overview-filter-box").jBox("Mouse", { ///
            theme: 'TooltipDark',
            content: 'Filter egos',
            position: {
              x: 'left',
              y: 'bottom'
           }
        });
        d3.select("#filter-ok").on("click", function(){
          // this_.$store.commit("changefilterIterms", this_.filterIterms);
          this_.jBoxInstance.filter.close();
        });
        d3.select("#cmp-ok").on("click", function(){
          this_.jBoxInstance.colorEncode.close();
        });
      },
      listenResized(eventName, realTimeParamList){
        let this_ = this;
        this_.leftBoxSplitSize = realTimeParamList[0].width; // left side
        this_.middleBoxSplitSize = realTimeParamList[1].width; // right side
      },
      mouseOverEvents(){
         $("#reflesh-block").jBox('Mouse', { // jBox在本文件中并没有引入,但是也能用(在mainView.vue中引入了).
              theme: 'TooltipDark',
              content: 'Refresh Overview',
              position: {
                x: 'left',
                y: 'bottom'
             }
        });
        $("#colormap-icon").jBox("Mouse", { ///
            theme: 'TooltipDark',
            content: 'Encode attributes in colors',
            position: {
              x: 'left',
              y: 'bottom'
           }
        });
        $("#legend-div-bx").jBox("Mouse", { ///
            theme: 'TooltipDark',
            content: 'Toggle Legend',
            position: {
              x: 'left',
              y: 'bottom'
           }
        });
      }      
    },

    components:{  // TODO: 注册组件后,就可以在template中像普通HTML元素一样使用,如<mainview></mainview>      
      Splitpanes, 
      Pane,
      selectdataset,
      egooverview,
      timelineslice,
      timelineslicerefresh,
      egonetsequences,
      timecurveview,
      searchbox,
      stackedgraph
    },
    computed: {
      //  ...mapState([
      //     "datasetList"
      // ])
    },
    watch:{
      rightBoxSplitSize:function(curVal, oldVal){
        if(curVal < 98){ // 右边视图扩大
           this.leftBoxSplitSize = 29;           
           this.rightBoxSplitSize = 71; // 右边
        }
      }      
    },
    mounted(){
      let this_ = this;
      console.log("App.vue mounted");
      this_.mouseOverEvents();
      // $("#distance-select").change(function(){
      //   let curVal = parseInt($(this).val());        
      //   // let getedText = this_.distanceOption[curVal]
      //   let whichDistance = this_.distanceOption[curVal].split(" ")[0].toLowerCase();
      //   // console.log("whichDistance");console.log(whichDistance);
      //   this_.$store.commit("changeselectedDistance", whichDistance);
      //   // bus.$emit("refreshMDSLayout", true);        
      // });
      $("#method-rd-select").change(function(){
        let curVal = parseInt($(this).val());
        let whichMethodRD = this_.methodRDOption[curVal];        
        this_.$store.commit("changeselectedMethodRD", whichMethodRD);
        // bus.$emit("refreshMDSLayout", true);
        // let allOptions = document.getElementById("method-norm-select").options;
        if(whichMethodRD == "PCA"){
          // for(let i=0; i<allOptions.length; i++){
          //   if(allOptions[i].label == "Z-Score"){ // ["None", "Min-Max", "Z-Score"],
          //       allOptions[i].selected = true;
          //       break;
          //   }
          // }
          this_.$store.commit("changeselectedMethodNorm", "Z-Score");
        }
        else{
          // for(let i=0; i<allOptions.length; i++){
          //   if(allOptions[i].label == "Min-Max"){ // ["None", "Min-Max", "Z-Score"],
          //       allOptions[i].selected = true;
          //       break;
          //   }
          // }
          this_.$store.commit("changeselectedMethodNorm", "Min-Max");
        }    
        
      }); 
      // $("#method-norm-select").change(function(){
      //   let curVal = parseInt($(this).val());
      //   let whichMethodNorm = this_.methodNorm[curVal];        
      //   this_.$store.commit("changeselectedMethodNorm", whichMethodNorm);
      //   // bus.$emit("refreshMDSLayout", true);        
      // });
      this_.jBoxInstance.filter = new jBox('Modal', {
            id: "jBoxFilter-overview",
            addClass: "jBoxFilterInfo-overview",  // 添加类型,这个功能很棒啊!
            attach: '.overview-filter-box',  // 这是历史走廊的图标.点击这个图标打开历史走廊弹窗.
            maxWidth: 250,            
            maxHeight: 450,
            adjustTracker:true,
            title: 'Filter Settings',
            overlay: false,
            zIndex: 1005, // fixme:注意多个jBox实例之间zIndex的值决定与最后一个实例.
            createOnInit: true,
            content: $("#overview-for-filter"),  // jQuery('#jBox-content') 
            draggable: false,
            repositionOnOpen: false,
            repositionOnContent: true,    
            target: $('#overview-filter-icon-img'),
            offset: {x: -10, y: 122},            
            onCloseComplete: function(){
               this_.$store.commit("changefilterIterms", this_.filterIterms);            
            }
      });
      this_.jBoxInstance.colorEncode = new jBox('Modal', {
            id: "jBoxColorEncode",
            addClass: "jBox-colormap",  // 添加类型,这个功能很棒啊!
            attach: '#colormap-icon',  // 这是历史走廊的图标.点击这个图标打开历史走廊弹窗.
            maxWidth: 250,            
            maxHeight: 450,
            adjustTracker:true,
            title: 'Encoding Colors for Attributes',
            overlay: false,
            zIndex: 1005, // fixme:注意多个jBox实例之间zIndex的值决定与最后一个实例.
            createOnInit: true,
            content: $("#map-attr-color"),  // jQuery('#jBox-content') 
            draggable: false,
            repositionOnOpen: false,
            repositionOnContent: true,    
            target: $('#colormap-icon-img'),
            offset: {x: -10, y: 86},            
            onCloseComplete: function(){
              let selectedAttr = this_.$store.getters.getattrRadio;
              let colorList = this_.$store.getters.getcolorSchemeObj[this_.$store.getters.getcolorRadio];
              let colorScheme = [colorList[0], colorList[colorList.length - 1]];
              this_.changeColorMap(selectedAttr, colorScheme, this_.$store.getters.getcolorRadio);          
            }
      });
      this_.jBoxInstance.legend = new jBox('Modal', {
            id: "jBoxLegend-overview",
            addClass: "jBoxLegendInfo-overview",  // 添加类型,这个功能很棒啊!
            attach: '#legend-div-bx',  // 这是历史走廊的图标.点击这个图标打开历史走廊弹窗.
            maxWidth: 250,            
            maxHeight: 450,
            adjustTracker:true,
            title: 'Legend for Multiple Views',
            overlay: false,
            zIndex: 1005, // fixme:注意多个jBox实例之间zIndex的值决定与最后一个实例.
            createOnInit: true,
            content: $("#overviews-for-legend"),  // jQuery('#jBox-content') 
            draggable: true,
            repositionOnOpen: false,
            repositionOnContent: true,                  
            // position:{x: 300, y: 350}
            target: $('#lgd-icon-img'),
            offset: {x: -10, y: 28}
      });
      this_.mouseEvents();
      this_.filterEvent();
    },
    updated(){
      console.log("App updated");
    },
    beforeDestroy(){      
      console.log("APP beforeDestroy");
      bus.$off("getobj4Filter");
    }
  }
</script>
<style>
  @import 'splitpanes/dist/splitpanes.css';
  @import "../static/css/frontend.css";
  @import "../static/css/jBox.css";  
</style>