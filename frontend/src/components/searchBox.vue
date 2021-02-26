<template>
  <div id="ego-search-box">    
    <div id="ego-search-div">
	    <el-autocomplete
	      size="mini"
	      class="input-box-keywords"
	      v-model="searchKeywords"
	      :fetch-suggestions="querySearch"
	      placeholder="Search here..."
	      @select="handleSearch">	    
	    	<el-select v-model="selectField" slot="prepend" placeholder="Select" class="select-field" @select="handleSelectField">
		      <el-option :label="item" :value="index" v-for="(item, index) in $store.getters.getfieldList"></el-option>		     
		    </el-select>
		    <el-button class="submit-search-keywords" slot="append" icon="el-icon-search"></el-button>
	    </el-autocomplete>
    </div>
    <div id="search-result-box">
        <el-table
        :data="tableSearchResult"
        :height="tableHeight"
        border        
        size="medium"        
        :row-class-name="tableRowClassName"
        @cell-mouse-enter="hoverCellHandle"
        @cell-mouse-leave="hoverCellLeaveHandle"
        @row-click="rowClickHandle"
        style="width: 100%">
        <el-table-column
          prop="ego"
          label="id"
          show-overflow-tooltip
          width="100">
        </el-table-column>
        <el-table-column :prop="item" :label="item" width="180" v-for="(item, index) in fieldList" show-overflow-tooltip>
        </el-table-column>        
      </el-table>
    </div>
  </div>  
</template>

<script>
  import * as d3 from '../../static/js/d3.v4.min.js'
  import {vueFlaskRouterConfig} from '../flaskRouter'
  import bus from '../eventbus.js' // 事件总线.  
  import axios from 'axios'
  import {jBox} from "../../static/js/jBox.js" 
  import $ from 'jquery'
  import "../../static/js/jquery.contextMenu.js"
  import "../../static/js/jquery.ui.position.js"
    
  export default {
    data() {
      return {           
          searchKeywords: '',
          selectField: "",
          tableHeight: 250,
          returnDataList: [], // 用于存储后他返回的数据
          jBoxInstance: {                
            searchResult: null, // 图例. jBoxInstance.searchResult
          },          
          fieldList: [],
          tableSearchResult: [], //[{ego: "mao", name: "mty", position: "CEO"}, {ego: "mao1", name: "mty1", position: "CEO1"}]
          previousKeywords: ""
      }
    },
    computed: {
      
    },
    watch: {
      searchKeywords: function(curVal, oldVal){
      	console.log(curVal);
      },
      selectField: function(curVal, oldVal){
      	let this_ = this;
      	let fieldVal = this_.$store.getters.getfieldList[parseInt(curVal)];
      	// console.log("fieldVal");console.log(fieldVal);
      	let param = {dbname: this_.$store.getters.getselectedDataset, field: fieldVal};
        axios.post(vueFlaskRouterConfig.getFieldAllVal, {
          param: JSON.stringify(param)
        })
        .then((res) => {
            this_.returnDataList.splice(0, this_.returnDataList.length);
            for(let i=0; i < res.data.length; i++){
		           let item = res.data[i];
		           this_.returnDataList.push(item);
		        }                  
                       
          })
        .catch((error) => {            
          console.error(error);
        });
      },
      tableSearchResult: function(curVal, oldVal){
        let this_ = this;
        if(curVal.length){
          this_.jBoxInstance.searchResult.open();
        }        
      }
    },
    methods: {
     tableRowClassName({row, rowIndex}) {
        let rowClass = "row-" + row.ego.replace(/\./g, "-");
        return rowClass;
     },
     rowClickHandle(row, column, event){
        let this_ = this;
        // console.log("jingjing row");console.log(row);
        if(this_.$store.getters.getselectedEgoList.indexOf(row.ego) == -1){ // 说明不在里面.
          this_.$store.commit("changeselectedEgoList", row.ego); // 首先添加到store.js中的selectedEgoList=["ego1", "ego2", ...]
          if(this_.$store.getters.getselectedDataset == "enron"){
            bus.$emit("selectDynamicEgonet", [row.ego, row.name + ": " + row.position]); // 发射信号,触发响应 
          }else{
            bus.$emit("selectDynamicEgonet", [row.ego, row.name]); 
          }        
          d3.select("#ego-overview-box circle." + "dyegovis-" + row.ego.replace(/\./g, "-")).attr("stroke", function(){
             // let idx = this_.$store.getters.getselectedEgoList.indexOf(row.ego);
             // let color = this_.$store.getters.getcolorSchemeList[idx];
             // return color;
             return "#de2d26";
          }).attr("stroke-width", 1); // 黑圈高亮
          d3.selectAll("#search-result-box tr.row-" + row.ego.replace(/\./g, "-") + ">td").attr("style", "background-color: #ecf5ff"); // 选中的row被高亮显示.
          d3.select("#ego-overview-box text.dyegovis-" + row.ego.replace(/\./g, "-")).attr("display", "block"); // 显示标签.
        }
     },
     hoverCellHandle(row, column, cell, event){
        let this_ = this;
        // console.log("row");console.log(row);        
        let circleClass = row.ego.replace(/\./g, "-"); // 变成"a-b-c"形式 
        d3.select("#ego-overview-box circle." + "dyegovis-" + circleClass).attr("fill", this_.$store.getters.getcolorMap.egoColor);
     },
     hoverCellLeaveHandle(row, column, cell, event){
        let this_ = this;
        // console.log("row searchbox");console.log(row);
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
        let circleClass = row.ego.replace(/\./g, "-"); // 变成"a-b-c"形式 
        // d3.select("#ego-overview-box circle." + "dyegovis-" + circleClass).attr("fill", this_.$store.getters.getcolorMap.pointColorObj[row.position]); // fixme: 中期时加的 this_.altersColor
        if(this_.$store.getters.getselectedDataset == "enron"){
          d3.select("#ego-overview-box circle." + "dyegovis-" + circleClass).attr("fill", function(){
            // this_.$store.getters.getcolorMap.pointColorObj[e.egoattrs.position]
            let attrVal = row[this_.$store.getters.getattrRadio];
            if(this_.$store.getters.getattrRadio == "position"){                                    
              return val2Color[attrVal]; 
            }else{ 
              // console.log("mouseout val2Color"); console.log(val2Color);                                                           
              return val2Color(attrVal);
            }
          }); // fixme: 中期时加的           
        }                      
        if(this_.$store.getters.getselectedDataset == "tvcg"){
          d3.select("#ego-overview-box circle." + "dyegovis-" + circleClass).attr("fill", function(){
            let attrVal = row[this_.$store.getters.getattrRadio];
            return val2Color(attrVal);
          }); // fixme: 中期时加的 
          if(this_.$store.getters.getclickedEgoList.indexOf(row.ego) == -1){
            d3.selectAll("#svg-egonets-time-step #all-overviews-g .overview-" + row.ego.replace(/\./g, "-"))
              .attr("stroke", "#d1d1d1")
              .attr("stroke-width", 1);
          }
        }
     },
  	 fuzzyQuery(list, keyWord) { // 模糊查询,从字符串中匹配出含有查询项的字符串.  	    
          let lowerCasekeyWord = keyWord.toLowerCase(); // 先转换成小写.
          let reg =  new RegExp(lowerCasekeyWord);
          let arr = [];
          if(list){
              for (let i = 0; i < list.length; i++) {
                let newStr = list[i].toLowerCase(); // 先转换成小写.
                if (reg.test(newStr)) {
                  let tempObj = {};
                  tempObj["value"] = list[i];                  
                  arr.push(tempObj);
                }
              }
          }                   
          return arr;        
  	 },
     querySearch(queryString, cb) {
     	  let this_ = this;        
        let allFieldData = this_.returnDataList; // [x, x, ...]        
        let results = this_.fuzzyQuery(allFieldData, queryString); // queryString实时输入的字符串, results必须是这种格式: [{value: x}, ...]        
        cb(results);
      },           
      handleSearch(item) { //当从下拉菜单选中某个值之后,触发该事件.
      	console.log("selected k");
        console.log(item);
      },
      handleSelectField(item){
        console.log("selected Field");
        console.log(item);
      },
      creatEvent(){
          let this_ = this;
          // 搜索事件
          $(".submit-search-keywords").on("click", function(){
          let queryItem = this_.searchKeywords;
          if(this_.previousKeywords != queryItem){ // 说明两次点击之间没有改变搜索词
            this_.previousKeywords = queryItem;
            let fieldVal = this_.$store.getters.getfieldList[parseInt(this_.selectField)];
            let param = {dbname: this_.$store.getters.getselectedDataset, field: fieldVal, queryKeywords: queryItem};
            axios.post(vueFlaskRouterConfig.getQueryResults, {
              param: JSON.stringify(param)
            })
            .then((res) => {
                           
                // console.log("getQueryResults"); console.log(res.data);
                this_.fieldList.splice(0, this_.fieldList.length);
                this_.fieldList.push("name");  
                this_.tableSearchResult = res.data;
                if(this_.tableSearchResult.length > 0){
                  let keyList = Object.keys(this_.tableSearchResult[0]);
                  keyList.forEach(function(item, index){
                     if(item != "ego" && item != "name"){
                      this_.fieldList.push(item);
                     }
                  });
                }
                
                if(res.data.length == 1){
                   this_.jBoxInstance.searchResult.setTitle("Search Result ("+ res.data.length + " row)");
                }else{
                  this_.jBoxInstance.searchResult.setTitle("Search Results ("+ res.data.length + " rows)");
                }
                       
              })
            .catch((error) => {            
              console.error(error);
            });
          }
          
        });       
        // $.contextMenu({          
        //     selector: '#search-result-box .el-table__row', // 绑定的元素,当在该元素右键时,就会弹出右键选择项目.
        //     className: "searchResultContextMenu",
        //     callback: function(key, options) {               
        //        if(key == "copy"){
        //          console.log("jingjign options");
        //          console.log(options);
        //          // console.log(options.$trigger["0"].attributes["0"].ownerElement.classList[1]); 
        //          let className = options.$trigger["0"].attributes["0"].ownerElement.classList[1]; // "row-mao-ting-yun"
        //          let egoClassStr = className.split("row-")[1]; // "a-b-c"
        //          let egoId = egoClassStr.replace(/\-/g, "."); // 获得ego的id.
        //          // console.log("egoClassStr egoId");console.log(egoId);
        //          // fixme: 下面计算出就演变模式而言, 与当前ego最相似的3个ego构成的序列.
        //          let egoPointPositionObj = this_.$store.getters.getegoPointPosition; // {ego0: [x, x, x, ...], ego1: [x, x, x, ...], ...}
        //          let curEgoPoint = egoPointPositionObj[egoId]; // 特征向量: [x, x, x, ...]
        //          let egoList = [];
        //          // egoList.push(egoId);
        //          let distanceList = [];
        //          // let disMetric = this_.$store.getters.getselectedDistance;
        //          let disMetric = "euclidean";
        //          for(let key in egoPointPositionObj){
        //             // if(key != egoId){
        //             egoList.push(key); // [ego0, ego1, ...]
        //             let dist = this_.computeDistancePoints(curEgoPoint, egoPointPositionObj[key], disMetric); // 计算点之间的距离.
        //             distanceList.push(dist); // [x, x, ...]
        //             // }
                    
        //          }
        //          let indexOfArr = this_.findIndexOfTopN(distanceList, 2);
        //          for(let i=0; i<indexOfArr.length; i++){ // indexOfArr=[0, 2]
        //             let indexEgo = indexOfArr[i];
        //             let selectedEgoId = egoList[indexEgo]; // 拿到ego的id,包括搜索结果表格中选中的节点.
        //             // console.log("selectedEgoId"); console.log(selectedEgoId);
        //             if(this_.$store.getters.getselectedEgoList.indexOf(selectedEgoId) == -1){ // 说明不在里面.
        //             this_.$store.commit("changeselectedEgoList", selectedEgoId); // 首先添加到store.js中的selectedEgoList=["ego1", "ego2", ...]
        //             bus.$emit("selectDynamicEgonet", selectedEgoId); // 发射信号,触发响应          
        //             d3.select("#ego-overview-box circle." + "dyegovis-" + selectedEgoId.replace(/\./g, "-")).attr("stroke", "black").attr("stroke-width", 2); // MDS空间布局中高亮选中的散点.
        //          }
        //          }

                 
                 
        //        }
               
        //     },
        //     items: {
        //         // "edit": {name: "Edit", icon: "edit"},
        //         // "cut": {name: "Cut", icon: "cut"},
        //         // "copy": {name: "Copy", icon: "copy"},
                
        //         "copy": {name: "Display its nearest sequence"},                
        //         "quit": {name: "Quit"}
        //     },
        //     zIndex: 1200
        //  });
      },
      // findIndexOfMinimum(array) { // 数值最小值的索引.
      //     let greatest;
      //     let indexOfGreatest;
      //     for (let i = 0; i < array.length; i++) {
      //       if (!greatest || array[i] < greatest) {
      //         greatest = array[i];
      //         indexOfGreatest = i;
      //       }
      //     }
      //     return indexOfGreatest; 
      // },
      minIndex(values, valueof) { // 数组最小值的索引
        let min;
        let minIndex = -1;
        let index = -1;
        if (valueof === undefined) {
          for (const value of values) {
            ++index;
            if (value != null
                && (min > value || (min === undefined && value >= value))) {
              min = value, minIndex = index;
            }
          }
        } else {
          for (let value of values) {
            if ((value = valueof(value, ++index, values)) != null
                && (min > value || (min === undefined && value >= value))) {
              min = value, minIndex = index;
            }
          }
        }
        return minIndex;
      },
      findIndexOfTopN(array, topN){
          let this_ = this;
          let indexOfArr = [];
          if(array.length <= topN){
             for(let i=0;i<array.length;i++){
                indexOfArr.push(i);
             }

          }
          else{
            let maxVal = d3.max(array); // 获得数组最大值.
            for(let i=0; i<topN; i++){
              let idx = this_.minIndex(array); // 找出数组最小值的索引
              indexOfArr.push(idx)
              array[idx]=maxVal; // 注意,这里改变了数组值.
            }
          }    
                   
          return indexOfArr;
      },
      computeDistancePoints(u, v, disMetric){ // todo: 核心:计算向量之间的相似性,使用余弦相似性.
          let len = u.length;
          // Canberra
          let distance = 0;
          if(disMetric == "canberra"){
            for ( let i = 0; i < len; i++ ) {
              let dif = u[i] - v[i];
              let difAbs = ( dif < 0 ) ? -dif : dif;
              let denom = ( ( u[i] < 0 ) ? -u[i] : u[i] ) + ( ( v[i] < 0 ) ? -v[i] : v[i] );
              distance += difAbs / denom;
            }
          }
          // Euclidean
          if(disMetric == "euclidean"){
              let sum = 0;
              for (let i = 0; i < len; i++) {
                  sum += Math.pow(u[i] - v[i], 2)
              }
              distance = Math.sqrt(sum);
          }
          return distance;
        
      }
    },
    created(){

    },
    mounted(){
      let this_ = this;
      this_.creatEvent();
      this_.jBoxInstance.searchResult = new jBox('Modal', {
                  id: "jBoxSearchResult",
                  addClass: "jBoxSearchResultInfo",  // 添加类型,这个功能很棒啊!
                  attach: '.submit-search-keywords',  // 这是历史走廊的图标.点击这个图标打开历史走廊弹窗.
                  maxWidth: 400,
                  // height: 200,
                  maxHeight: this_.tableHeight,
                  adjustTracker:true,
                  title: 'Search Result',
                  overlay: false,
                  zIndex: 1005, // fixme:注意多个jBox实例之间zIndex的值决定与最后一个实例.
                  createOnInit: true,
                  content: $("#search-result-box"),  // jQuery('#jBox-content') 
                  draggable: false,
                  repositionOnOpen: false,
                  repositionOnContent: true,    
                  target: $('#ego-search-div'),
                  offset: {x: -90, y: 150}              
                  // position:{x: 300, y: 150}
       });        
    },
    updated(){
      console.log("searchBox updated");
    }
  }
</script>
<style>
@import "../../static/css/jquery.contextMenu.css"; 
#ego-search-box #search-result-box td > div{
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
    
</style>>