<template>
  <div id="time-slice-refresh">           
    <div class="slice-class" id="reflesh-time-slice">
      <div v-show='$store.getters.getselectedDataset' id='reflesh-block' class="widget-tool">
        <img class="img-icon" id="reflesh-img" width="20" height="20" src="../../static/img/refresh.svg">
      </div>
    </div>
  </div>  
</template>

<script>
  import * as d3 from '../../static/js/d3.v4.min.js'
  import {vueFlaskRouterConfig} from '../flaskRouter'
  import bus from '../eventbus.js' // 事件总线.  
  import axios from 'axios'
  import {jBox} from "../../static/js/jBox.js" 
    
  export default {
    data() {
      return {           
               
      }
    },
    computed: {
      
    },
    watch: {
      
    },
    methods: {
      refreshAction(){
          let this_ = this;
          d3.select("#all-dyegonets").remove(); // 清除svg中旧的内容.
          d3.selectAll("#track-lines-g g").remove(); // 将原来的边擦除掉.  
          d3.select("#svg-dyegonet").attr("height", 0);
          d3.select("#svg-dyegonet-bg").attr("height", 0);                
          d3.select("#svg-dyegonet").append("g")
                                    .attr("id", "all-dyegonets")
                                    .attr("transform", "translate(10,10)");
          d3.selectAll("#svg-dyegonet #gcompLines > *").remove();
          d3.selectAll("#svg-egonets-time-step #all-overviews-g > *").remove(); // 之前使用select, 应该使用selectAll.
          this_.$store.commit("clearselectedEgoList"); // 清除egolist.
          let timeInterval = this_.$store.getters.gettimeStepSlice; // [2000-02, 2002-01]
          let timeStepList = this_.$store.getters.gettimeStepList; // [x, x, ...]
          if(timeStepList[0] == timeInterval[0] && timeStepList[timeStepList.length - 1] == timeInterval[1]){
             timeInterval = [];
          }
          // console.log("this_.$store.getters.getselectedMethodNorm");console.log(this_.$store.getters.getselectedMethodNorm);
          let param = {dbname: this_.$store.getters.getselectedDataset, timeInterval: timeInterval, whichDistance: this_.$store.getters.getselectedDistance, whichMethodRD:this_.$store.getters.getselectedMethodRD, whichMethodNorm: this_.$store.getters.getselectedMethodNorm, filterCond: this_.$store.getters.getfilterIterms};
          // console.log("this_.$store.getters.getfilterIterms");console.log(this_.$store.getters.getfilterIterms);
          axios.post(vueFlaskRouterConfig.timeSliceRefresh, {
            param: JSON.stringify(param)
          })
          .then((res) => {                   
                  // console.log("timeLineSliceRefresh respond data"); console.log(res.data);
               bus.$emit("getEgoVecObj", res.data.egoPointList);                
               bus.$emit("getOverviewTimeSteps", res.data.overviewTimeSteps); 
                     
            })
          .catch((error) => {            
            console.error(error);
          });
          this_.$store.commit("clearAllselectedEgoObj");
          this_.$store.commit("clearegoOverviewTimeStepRt");
          this_.$store.commit("clearegoNetSequenceRt");
      }
    },
    created(){
      let this_ = this;
      bus.$on("refreshMDSLayout", function(data){
         if(data){
            this_.refreshAction();
         }
      });
    },
    mounted(){
      let this_ = this;      
      d3.select("#reflesh-block").on("click", function () {
          this_.refreshAction();
      });
      
    },
    updated(){
      console.log("timeLineSliceRefresh updated");
    },
    beforeDestroy(){
      console.log("egoNetSequences beforeDestroy");
      bus.$off("refreshMDSLayout");
    }
  }
</script>
<style> 
  
</style>>