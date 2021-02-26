<template>
  <div id="time-line-slice">
    <div v-if='$store.getters.getselectedDataset' id='slice-label-box'>
      <img width="10" height="10" src="../../static/img/calendar.svg" style="display:inline-block">
      <label id="slice-label">{{showTimeSlice}}</label> 
    </div>
    <div class="slice-class" id='time-slider'></div>       
  </div>  
</template>

<script>
  import * as d3 from '../../static/js/d3.v4.min.js'
  import {vueFlaskRouterConfig} from '../flaskRouter'
  import bus from '../eventbus.js' // 事件总线.  
  import axios from 'axios'  
  import * as noUiSlider from '../../static/js/noUiSlider.js'
  import {mapGetters} from 'vuex'

  export default {
    data() {
      return {
         slider: null,
         showTimeSlice: null                      
      }
    },
    computed: {
      ...mapGetters([
          "gettimeStepList",
          "gettimeStepSlice"
        ])
    },
    watch: {
      gettimeStepList: function (curVal, oldVal){ // 当加载完数据后, 时间线更新时, 创建一个时间线滑道.
        let this_ = this;
        // console.log("timeLineSlice gettimeStepList");console.log(curVal);
        noUiSlider.create(this_.slider, {
            start: [0, curVal.length - 1],
            step: 1,
            tooltips: false,
            behaviour: 'drag',
            connect: true,
            range: {
                'min': 0,
                'max': curVal.length - 1
            }
          
        });
        this_.sliderEvent(curVal);
      },
      gettimeStepSlice: function(curVal, oldVal){
        let this_ = this;
        let tempStr = '';
        if(curVal[0] == curVal[1]){
          tempStr = curVal[0];
        }
        else{
          tempStr = curVal[0] + " - " + curVal[1];
        }
        this_.showTimeSlice = tempStr;
      }
    },
    methods: {
      // restoreTimeSlider(){ // 恢复滑道的初始位置.
      //   let this_ = this;
      //   if(this_.$store.getters.gettimeStepList.length > 0){
      //     d3.select(".noUi-handle-lower").attr("aria-valuenow", 0).attr("aria-valuetext", 0);
      //     d3.select(".noUi-handle-upper").attr("aria-valuenow", this_.$store.getters.gettimeStepList.length).attr("aria-valuetext", this_.$store.getters.gettimeStepList.length);
      //   }        
      // },
      sliderEvent(timeStepList){ // 存在一个不足, 当切换数据库时, 时间滑道不归位, 所以想要切换数据时, 先将滑道复位.
        let this_ = this;
        this_.slider.noUiSlider.on('start', function (values, handle) { 
             // console.log("start values"); console.log(values);
             let minTimeStep, maxTimeStep;            
             // let minTimeStep = timeStepList[0];
             // let maxTimeStep = timeStepList[timeStepList.length - 1];
             if (handle) {              
                  let maxVal = Math.round(values[handle]); // [timeStepList[Math.round(values[0])], timeStepList[Math.round(values[1])]]
                  maxTimeStep = timeStepList[maxVal];
                  d3.select(".noUi-active .noUi-tooltip").html(maxTimeStep);                  
              } else {
                 let minVal = Math.round(values[handle]);
                 minTimeStep = timeStepList[minVal];
                 d3.select(".noUi-active .noUi-tooltip").html(minTimeStep);                 
              }
              // console.log("start [minTimeStep, maxTimeStep]"); console.log([timeStepList[Math.round(values[0])], timeStepList[Math.round(values[1])]]);
              this_.$store.commit("changetimeStepSlice", [timeStepList[Math.round(values[0])], timeStepList[Math.round(values[1])]]);
        });
        this_.slider.noUiSlider.on('update', function (values, handle) {
            // console.log("update values"); console.log(values);
            let minTimeStep, maxTimeStep;
            // let minTimeStep = timeStepList[0];
            // let maxTimeStep = timeStepList[timeStepList.length - 1];
            if (handle) {              
                let maxVal = Math.round(values[handle]);
                maxTimeStep = timeStepList[maxVal];
                d3.select(".noUi-active .noUi-tooltip").html(maxTimeStep);                
            } else {
               let minVal = Math.round(values[handle]);
               minTimeStep = timeStepList[minVal];
               d3.select(".noUi-active .noUi-tooltip").html(minTimeStep);               
            }
            // console.log("update [minTimeStep, maxTimeStep]"); console.log([timeStepList[Math.round(values[0])], timeStepList[Math.round(values[1])]]);
            this_.$store.commit("changetimeStepSlice", [timeStepList[Math.round(values[0])], timeStepList[Math.round(values[1])]]);
        });
      }
    },
    created(){

    },
    mounted(){
      let this_ = this;
      this_.slider = document.getElementById('time-slider');      
    },
    updated(){
      console.log("timeLineSlice updated");
    }
  }
</script>
<style>
  @import "../../static/css/nouislider.css";
   
</style>>