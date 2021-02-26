<template>		    
	 <div id=select-dataset>
    <span class="md-name">Dataset:</span>     
    <el-select 
      v-model="selectedDataset"
      size="mini" 
      filterable
      @visible-change="dropDownBoxVisible" 
      placeholder="Select">
      <el-option
          v-for="(item, index) in $store.getters.getdatasetList"
          :key="item"
          :label="item"
          :value="item">
      </el-option>
    </el-select>
   </div>		
</template>

<script>
  // eslint-disable-next-line
  /* eslint-disable */
  import * as d3 from '../../static/js/d3.v4.min.js'
  import {vueFlaskRouterConfig} from '../flaskRouter'
  import bus from '../eventbus.js' // 事件总线.
  import axios from 'axios'
  import $ from 'jquery'
  // import { mapState } from 'vuex'

  export default {   
    data(){
      return {
        selectedDataset: null        
      }
    },
    computed: {
       // ...mapState([
       //   "selectedDataset"
       //  ])
    },
    watch: {
      selectedDataset: function(curVal, oldVal){
        d3.select("#all-dyegonets").remove(); // 清除svg中旧的内容.
        d3.selectAll("#track-lines-g g").remove(); // 将原来的边擦除掉.  
        d3.select("#svg-dyegonet").attr("height", 0);
        d3.select("#svg-dyegonet-bg").attr("height", 0);
        d3.select("#svg-dyegonet").append("g")
                                  .attr("id", "all-dyegonets")
                                  .attr("transform", "translate(10,10)");

        let this_ = this;
        // this_.restoreTimeSlider(); // 如果滑道移动过,则恢复初始位置.
        // console.log("this_.$store.getters.getselectedMethodNorm");console.log(this_.$store.getters.getselectedMethodNorm);
        this_.$store.commit('changeselectedDataset', curVal); // change the state 'selectedDataset'
        let param = {dbname: curVal, whichDistance: this_.$store.getters.getselectedDistance, whichMethodRD: this_.$store.getters.getselectedMethodRD, whichMethodNorm: this_.$store.getters.getselectedMethodNorm};
        axios.post(vueFlaskRouterConfig.selectdataset, {
          param: JSON.stringify(param)
        })
        .then((res) => { 
                bus.$emit("getobj4Filter", res.data.obj4Filter);
                this_.$store.commit("changefeatureNameList", res.data.ftNamels);
                // 初始化选择的属性.
                if(this_.$store.getters.getselectedDataset == "enron"){                  
                  this_.$store.commit("changeattrRadio", "position");
                }
                if(this_.$store.getters.getselectedDataset == "tvcg"){                 
                  this_.$store.commit("changeattrRadio", "total_p_num");
                }     
                bus.$emit("getEgoVecObj", res.data.egoPointList);
                let attrOptions = Object.keys(res.data.egoPointList[0].egoattrs); // ["name", ...]                
                attrOptions.splice(attrOptions.indexOf("name"), 1);                
                this_.$store.commit("changegetCandidateAttrs", attrOptions);               
                this_.$store.commit('changetimeStepList', res.data.timeStepList); // 初始化时间步列表.
                this_.$store.commit("changetimeStepSlice", [res.data.timeStepList[0], res.data.timeStepList[res.data.timeStepList.length - 1]]); // 初始化时间切片列表.由于之前没有初始化导致发生错误.
                this_.$store.commit("changefieldList", res.data.fieldList); 
                bus.$emit("getOverviewTimeSteps", res.data.overviewTimeSteps); // bus.$emit("getEgoVecObj", res.data.egoPointList);
          })
        .catch((error) => {            
          console.error(error);
        });
        // this_.$store.commit("changegetFilterInfoFlag", false);
        this_.$store.commit("clearAllselectedEgoObj");
        this_.$store.commit("clearegoOverviewTimeStepRt");
        this_.$store.commit("clearegoNetSequenceRt");
        if(oldVal){
          d3.selectAll("#svg-dyegonet #gcompLines > *").remove();
        }
        this_.$store.commit("clearmarkRectTextList"); 
      }
    },
    components: {
     
    },
    methods:{
      // restoreTimeSlider(){ // 恢复滑道的初始位置.
      //   let this_ = this;
      //   if(this_.$store.getters.gettimeStepList.length > 0){
      //     $(".noUi-origin").eq(0).attr("style", "transform: translate(-1000%, 0px); z-index: 5;");
      //     $(".noUi-origin").eq(1).attr("style", "transform: translate(0%, 0px); z-index: 5;");
      //     d3.select(".noUi-handle-lower").attr("aria-valuenow", 0).attr("aria-valuetext", 0);
      //     d3.select(".noUi-handle-upper").attr("aria-valuenow", this_.$store.getters.gettimeStepList.length).attr("aria-valuetext", this_.$store.getters.gettimeStepList.length);
      //   }        
      // },
      dropDownBoxVisible(){
        let this_ = this;
        console.log("selecting dataset");
      },
      processEgoVecObj(egoVecObj){
        // egoVecObj: {'ego1': [x, x, ...], ...}
        let this_ = this;


      }
    },
    created(){
      console.log("created");
      
    },
    mounted(){
      console.log("mounted");
      let this_ = this;  
      
    },
    updated(){
      console.log("selectDataset updated");
    },
    beforeDestroy(){
      console.log("selectdataset beforeDestroy");
    }   
  }
</script>

<style>


</style>