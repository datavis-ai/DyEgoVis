<template>
  <div id="stacked-g-box">
    <div id="stack-nav-box">
    	<div id="lgd-stg"></div>
    	<div id="slct-ft-stg">		 
         <span class="md-name">Select a feature:</span>
         <el-select size="mini" v-if="$store.getters.getfeatureNameList" v-model="slctFt" placeholder="Select">
		    <el-option		      
		      v-for="item in $store.getters.getfeatureNameList"
		      :key="item"
		      :label="item"
		      :value="item">
		    </el-option>
		 </el-select>
    	</div>
    </div>
	<div id="stacked-area"></div>
  </div>
</template>
<script>
  // eslint-disable-next-line
  /* eslint-disable */
  import * as d3 from '../../static/js/d3.v4.min.js'
  import {vueFlaskRouterConfig} from '../flaskRouter'
  import bus from '../eventbus.js' // 事件总线.
  import axios from 'axios'
  import {jBox} from "../../static/js/jBox.js"
  // import { mapState } from 'vuex'

  export default {    
    data(){
      return {
      	slctFt: "num_alters",      	
		jBoxInstance:{ // 弹出窗口          
          stackedArea: null
        }
      }
    },
    computed: {       
    },
    watch: {
      slctFt: function(curVal, oldVal){
      	this.getStackedData();
      }
    },
    components: {
     
    },
    methods:{
      getStackedData(){
      	  let this_ = this;
      	  if(this_.$store.getters.getselectedEgoList.length > 0){
      	  	  let timeInterval = this_.$store.getters.gettimeStepSlice; // [2000-02, 2002-01]
		      let timeStepList = this_.$store.getters.gettimeStepList; // [x, x, ...]
		      if(timeStepList[0] == timeInterval[0] && timeStepList[timeStepList.length - 1] == timeInterval[1]){
		         timeInterval = [];
		      }       
		      let param = {dbname: this_.$store.getters.getselectedDataset, timeInterval: timeInterval, selectedegolist: this_.$store.getters.getselectedEgoList, feature: this_.slctFt};
		      axios.post(vueFlaskRouterConfig.getStackedGraph, {
		        param: JSON.stringify(param)
		      })
		      .then((res) => {                   
		          // console.log("startStackedG res.data"); console.log(res.data);
		          let margin = {top: 2, right: 18, bottom: 18, left: 18},
			          width = 1302 - margin.left - margin.right,
			          height = 120 - margin.top - margin.bottom;
		          this_.drawStackedGraph(res.data, width, height, margin);
		        })
		      .catch((error) => {            
		        console.error(error);
		      });
      	  }else{
      	  	d3.selectAll('#stacked-area > *').remove();
      	  }	  	  
      },
      drawStackedGraph(stackedData, width, height, margin){
		let this_ = this;      	
	    let data = stackedData.dataList;	    
	    let x = d3.scaleTime()
	        .range([0, width]);
	    let y = d3.scaleLinear()
	        .range([height, 0]);
	    let xAxis = null;
	    let parseDate = null;
	    if(this_.$store.getters.getselectedDataset == "enron"){
	    	parseDate = d3.timeParse("%Y-%m");
	    	xAxis = d3.axisBottom()
			          .scale(x)
			          .ticks(data.length) // 刻度
			          .tickFormat(d3.timeFormat("%Y-%m")); // 修改X轴的格式.
	    }else{
	    	parseDate = d3.timeParse("%Y");
	    	xAxis = d3.axisBottom()
			          .scale(x)
			          .ticks(data.length) // 刻度
			          .tickFormat(d3.timeFormat("%Y")); // 修改X轴的格式.
	    }

	    let area = d3.area()
	        .x(function(d){
	          return x(d.data.date);})
	        .y0(function(d) {return y(d[0]);})
	        .y1(function(d) {return y(d[1]);});
	    let stack = d3.stack();
	    d3.selectAll('#stacked-area > *').remove();
	    let svg = d3.select('#stacked-area').append('svg')
	        .attr('width', width + margin.left + margin.right)
	        .attr('height', height + margin.top + margin.bottom)
	        .append('g')
	        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

	    let keys = stackedData.columns.filter(function(key) { return key !== 'date'; });
	    // console.log("stackedData.columns"); console.log(keys);
	    keys = keys.reverse(); // fixme: 这样做是为了将堆叠的顺序逆转, 按照dyegonet的顺序排列.
	    // console.log("keys.reverse"); console.log(keys);
	    data.forEach(function(d) { // data = [{}, ...], 其中元素: {date: x, key1: x, ...}
	    d.date = parseDate(d.date);
	    });
	    /*
	    data = [{date: 1990, A: 10, B: 20, C: 30}, ...] data.length == total timesteps
	    */
	    let maxDateVal = d3.max(data, function(d){ // d={key1: x, ...}
	    let vals = d3.keys(d).map(function(key){ return key !== 'date' ? d[key] : 0 }); // [val1, val2, ...]
	    return d3.sum(vals); // 每个时间步下累计和
	    }); // [sum1, sum2, ...] 长度 == 时间跨度内的总时间步数, 然后从中取得最大值.
	    // console.log("data");
	    // console.log(data);
	    // Set domains for axes
	    x.domain(d3.extent(data, function(d){return d.date;})); // [min_date, max_date]
	    y.domain([0, maxDateVal]);
	    stack.keys(keys); // keys: [A, B, C]
	    stack.order(d3.stackOrderNone);
	    stack.offset(d3.stackOffsetNone);
	    let browser = svg.selectAll('.browser')
	      .data(stack(data)) // stack(data): [[[y1, y2], ...], ...]
	      .enter().append('g')
	      .attr('class', function(d){ return 'browser ' + d.key; })
	      .attr('fill-opacity', 0.5);

	    browser.append('path')
	      .attr('class', 'area')
	      .attr('d', area)
	      .style('fill', function(d) {
	      	return this_.$store.getters.getcolorSchemeList[stackedData.columns.indexOf(d.key) - 1];
	      	// return color(d.key); 
	      });

	    svg.append('g')
	      .attr('class', 'x axis')
	      .attr('transform', 'translate(0,' + height + ')')
	      .call(xAxis);
	  }
    },
    created(){
      let this_ = this;
      console.log("stackedGraph created");
      // vueFlaskRouterConfig.getStackedGraph
      bus.$on('startStackedG', function (data){            
        if(data){
          this_.getStackedData();
        }
      }); 
      
    },
    mounted(){
      console.log("stackedGraph mounted");
      let this_ = this;
      // this_.featureOptions = Object.keys(this_.$store.getters.getfilterIterms); // [x, x, ...]
      this_.jBoxInstance.stackedArea = new jBox("Modal", {
            id: "jBox-stackedArea",
            addClass: "jBox-sta",  // 添加类型,这个功能很棒啊!
            attach: '.egonetseq-legend-box',  // 这是历史走廊的图标.点击这个图标打开历史走廊弹窗.
            maxWidth: 1302,            
            maxHeight: 200,
            // adjustTracker:true,
            title: 'Feature Evolution',
            overlay: false,
            zIndex: 1005, // fixme:注意多个jBox实例之间zIndex的值决定与最后一个实例.
            createOnInit: true,
            content: $("#stacked-g-box"),  // jQuery('#jBox-content') 
            draggable: true,
            repositionOnOpen: false,
            repositionOnContent: true,    
            // target: $('#ego-overview-box'),
            offset: {x: 270, y: 380},            
            onCloseComplete: function(){
               // let egoId = this_.curViewEgo;                         
            }
      }); 
      
    },
    updated(){
      console.log("stackedGraph updated");
    },
    beforeDestroy(){
      console.log("stackedGraph beforeDestroy");
      bus.$off("startStackedG");
    }   
  }
</script>