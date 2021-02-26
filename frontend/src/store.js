import Vue from 'vue'
import Vuex from 'vuex'
Vue.use(Vuex); // 使用vue插件, vue.use(插件)

const store = new Vuex.Store({  // 用const意味着地址不变,而对象的键值对是可以更改的.
  state: {
    colorMap: {
      egoColor: "#1890ff", // 鼠标悬浮,ego显示的颜色.
      pointColorObj: {"CEO": "#4C0016", "President": "#62202D", "Vice President":"#794044", "Director": "#8F605A", "Managing Director": "#A68071", "Manager": "#BC9F88", "In House Lawyer":"#D2BF9F", "Trader": "#E9DFB5", "Employee": "#FFFFCC", "unknown": "white"}, 
      pointColorShObj:{      
        'sch1': {'Manager': '#9E7D81', 'unknown': '#DFD4D5', 'In House Lawyer': '#AE9296', 'Director': '#7E5157', 'Vice President': '#6D3B42', 'President': '#5D262D', 'Employee': '#CEBEC0', 'Managing Director': '#8E676C', 'Trader': '#BEA8AB', 'CEO': '#4D1018'}, 
        'sch2': {'Manager': '#B88187', 'unknown': '#E7D5D7', 'In House Lawyer': '#C3969B', 'Director': '#A0575F', 'Vice President': '#94424B', 'President': '#882D37', 'Employee': '#DBC0C3', 'Managing Director': '#AC6C73', 'Trader': '#CFABAF', 'CEO': '#7C1823'}, 
        'sch3': {'Manager': '#9E8B97', 'unknown': '#DFD8DC', 'In House Lawyer': '#AF9EA8', 'Director': '#7E6474', 'Vice President': '#6E5163', 'President': '#5E3D51', 'Employee': '#CFC5CB', 'Managing Director': '#8E7785', 'Trader': '#BFB2BA', 'CEO': '#4E2A40'}, 
        'sch4': {'Manager': '#8D8FB8', 'unknown': '#D9DAE7', 'In House Lawyer': '#A0A1C3', 'Director': '#6769A0', 'Vice President': '#545694', 'President': '#414488', 'Employee': '#C6C7DB', 'Managing Director': '#7A7CAC', 'Trader': '#B3B4CF', 'CEO': '#2E317C'},
        'sch5': {'Manager': '#8EC2D9', 'unknown': '#D9EBF2', 'In House Lawyer': '#A0CDDF', 'Director': '#68AECC', 'Vice President': '#55A4C6', 'President': '#429ABF', 'Employee': '#C6E1EC', 'Managing Director': '#7BB8D2', 'Trader': '#B3D7E6', 'CEO': '#2F90B9'}, 
        'sch6': {'Manager': '#82AD97', 'unknown': '#D5E4DC', 'In House Lawyer': '#97BAA8', 'Director': '#589174', 'Vice President': '#448363', 'President': '#2F7651', 'Employee': '#C1D6CB', 'Managing Director': '#6D9F85', 'Trader': '#ACC8BA', 'CEO': '#1A6840'},
        'sch7': {'Manager': '#FFB97C', 'unknown': '#FFE8D3', 'In House Lawyer': '#FFC591', 'Director': '#FFA250', 'Vice President': '#FF963A', 'President': '#FF8B24', 'Employee': '#FFDCBD', 'Managing Director': '#FFAE66', 'Trader': '#FFD0A7', 'CEO': '#FF7F0E'},
        'sch8': {'Manager': '#80BAD7', 'unknown': '#D5E8F2', 'In House Lawyer': '#96C6DD', 'Director': '#56A3C9', 'Vice President': '#4198C2', 'President': '#2C8CBC', 'Employee': '#C0DDEB', 'Managing Director': '#6BAFD0', 'Trader': '#ABD1E4', 'CEO': '#1781B5'},
        'sch9': {"CEO": "#4C0016", "President": "#62202D", "Vice President":"#794044", "Director": "#8F605A", "Managing Director": "#A68071", "Manager": "#BC9F88", "In House Lawyer":"#D2BF9F", "Trader": "#E9DFB5", "Employee": "#FFFFCC", "unknown": "white"}
      }
      
    },
    egoOverview: {
      selectedDataset: null, // 'enron'
    },
    selectDataset: {
      datasetList: [], // database name , e.g., ["enron", ...]
    },  
    timeLineSlice: { // timeLineSlice.timeStepList
      timeStepList: [], // the whole timeline: ['2000-03', '2000-04', ..., '2002-02']
      timeStepSlice: [] // the selected time sclice: ['2000-06', '2000-09']
    },
    egoNetSequences: {
      selectedEgoList: [], // [ego1, ego2, ...]
      markRectTextList: [] // [[rect, text], ...]
    },
    App: {
      selectedDistance: "canberra",
      selectedMethodRD: "PCA",  //布局方式.
      selectedMethodNorm: "Z-Score", // 标准化: None, Min-Max, z-score      
      filterIterms: null, // 过滤条件
      getCandidateAttrs: null,
      // colorSchemeObj: {
      //     sch1: ['#f7fbff','#deebf7','#c6dbef','#9ecae1','#6baed6','#4292c6','#2171b5','#08519c','#08306b'],
      //     sch2: ['#f7fcf5','#e5f5e0','#c7e9c0','#a1d99b','#74c476','#41ab5d','#238b45','#006d2c','#00441b'],
      //     sch3: ['#ffffff','#f0f0f0','#d9d9d9','#bdbdbd','#969696','#737373','#525252','#252525','#000000'],
      //     sch4: ['#fff5eb','#fee6ce','#fdd0a2','#fdae6b','#fd8d3c','#f16913','#d94801','#a63603','#7f2704'],
      //     sch5: ['#fcfbfd','#efedf5','#dadaeb','#bcbddc','#9e9ac8','#807dba','#6a51a3','#54278f','#3f007d'],
      //     sch6: ['#fff5f0','#fee0d2','#fcbba1','#fc9272','#fb6a4a','#ef3b2c','#cb181d','#a50f15','#67000d'],
      //     sch7: ["white", "#FFFFCC", "#E9DFB5", "#D2BF9F", "#BC9F88", "#A68071", "#8F605A", "#794044", "#62202D", "#4C0016"]
      //  },
      colorSchemeObj:{
        sch1: ["#EFE9EA", "#DFD4D5", "#CEBEC0", "#BEA8AB", "#AE9296", "#9E7D81", "#8E676C", "#7E5157", "#6D3B42", "#5D262D", "#4D1018"],
        sch2: ["#F3EAEB", "#E7D5D7", "#DBC0C3", "#CFABAF", "#C3969B", "#B88187", "#AC6C73", "#A0575F", "#94424B", "#882D37", "#7C1823"],
        sch3: ["#EFECEE", "#DFD8DC", "#CFC5CB", "#BFB2BA", "#AF9EA8", "#9E8B97", "#8E7785", "#7E6474", "#6E5163", "#5E3D51", "#4E2A40"],
        sch4: ["#ECECF3", "#D9DAE7", "#C6C7DB", "#B3B4CF", "#A0A1C3", "#8D8FB8", "#7A7CAC", "#6769A0", "#545694", "#414488", "#2E317C"],
        sch5: ["#ECF5F9", "#D9EBF2", "#C6E1EC", "#B3D7E6", "#A0CDDF", "#8EC2D9", "#7BB8D2", "#68AECC", "#55A4C6", "#429ABF", "#2F90B9"],
        sch6: ["#EAF1EE", "#D5E4DC", "#C1D6CB", "#ACC8BA", "#97BAA8", "#82AD97", "#6D9F85", "#589174", "#448363", "#2F7651", "#1A6840"],
        sch7: ["#FFF3E9", "#FFE8D3", "#FFDCBD", "#FFD0A7", "#FFC591", "#FFB97C", "#FFAE66", "#FFA250", "#FF963A", "#FF8B24", "#FF7F0E"], // ["#FEF3EA", "#FEE7D6", "#FDDCC1", "#FDD0AC", "#FCC498", "#FCB883", "#FBAC6F", "#FBA05A", "#FA9545", "#FA8931", "#F97D1C"],        
        sch8: ["#EAF4F8", "#D5E8F2", "#C0DDEB", "#ABD1E4", "#96C6DD", "#80BAD7", "#6BAFD0", "#56A3C9", "#4198C2", "#2C8CBC", "#1781B5"],
        sch9: ["#FFFFC0", "#FFFFCC", "#E9DFB5", "#D2BF9F", "#BC9F88", "#A68071", "#8F605A", "#794044", "#62202D",  "#4C0016", "#4C001B"]
        // sch1: ["#DFD4D5", "#CEBEC0", "#BEA8AB", "#AE9296", "#9E7D81", "#8E676C", "#7E5157", "#6D3B42", "#5D262D", "#4D1018"],
        // sch2: ["#E7D5D7", "#DBC0C3", "#CFABAF", "#C3969B", "#B88187", "#AC6C73", "#A0575F", "#94424B", "#882D37", "#7C1823"],
        // sch3: ["#DFD8DC", "#CFC5CB", "#BFB2BA", "#AF9EA8", "#9E8B97", "#8E7785", "#7E6474", "#6E5163", "#5E3D51", "#4E2A40"],
        // sch4: ["#D9DAE7", "#C6C7DB", "#B3B4CF", "#A0A1C3", "#8D8FB8", "#7A7CAC", "#6769A0", "#545694", "#414488", "#2E317C"],
        // sch5: ["#D9EBF2", "#C6E1EC", "#B3D7E6", "#A0CDDF", "#8EC2D9", "#7BB8D2", "#68AECC", "#55A4C6", "#429ABF", "#2F90B9"],
        // sch6: ["#D5E4DC", "#C1D6CB", "#ACC8BA", "#97BAA8", "#82AD97", "#6D9F85", "#589174", "#448363", "#2F7651", "#1A6840"],
        // sch7: ["#FFE8D3", "#FFDCBD", "#FFD0A7", "#FFC591", "#FFB97C", "#FFAE66", "#FFA250", "#FF963A", "#FF8B24", "#FF7F0E"], // ["#FEF3EA", "#FEE7D6", "#FDDCC1", "#FDD0AC", "#FCC498", "#FCB883", "#FBAC6F", "#FBA05A", "#FA9545", "#FA8931", "#F97D1C"],        
        // sch8: ["#D5E8F2", "#C0DDEB", "#ABD1E4", "#96C6DD", "#80BAD7", "#6BAFD0", "#56A3C9", "#4198C2", "#2C8CBC", "#1781B5"],
        // sch9: ["#FFFFFF", "#FFFFCC", "#E9DFB5", "#D2BF9F", "#BC9F88", "#A68071", "#8F605A", "#794044", "#62202D",  "#4C0016"]
      },
      colorRadio: "sch1", // this_.$store.state.colorRadio
      attrRadio: null, // this_.$store.state.attrRadio
      filterObj: null // 后端响应的过滤信息: {f1: [min, max], ...}
    },
    searchBox: {
      fieldList: [],
      egoPointPosition: null, // {ego0: [x, y], ...}
    },
    egoOverviewTimeStep: {
      timeStepEgonetW: 180, // 每个时间步下egonet所占宽度.
      timeStepEgonetH: 180, // 每个时间步下egonet所占高度.
      timeStepOverviewH: 160, // 时间步概览的高度.
      clickedEgoList: [], // [egoId, ...]
      dateStringArray: [] // [2000-02, 2000-03, ...]
    },
    timeCurveView:{
      colorSchemeList: ['#8dd3c7','#bebada','#fb8072','#80b1d3','#fdb462','#b3de69','#fccde5','#d9d9d9'],
      selectedEgoObj: {} // {ego1: name, ego2: name, ...}
    },
    DOM:{
      egoOverviewRt: null, // egoOverviewRt egoNetSequenceRt egoOverviewTimeStepRt      
      egoOverviewTimeStepRt: [], // [x, x, ...]
      egoNetSequenceRt: [] // [[x, x, ...], [x, x, ...], ...]
    },
    stackedGraph:{
      featureNameList: null
    }
  },
  getters: {  // 读取state的值,简化组件中读取state的代码.类似于computed属性,调用的时不用加(),e.g. state.xxx, 而非state.xxx()
    getfeatureNameList(state){ // this_.$store.getters.getfeatureNameList
      return state.stackedGraph.featureNameList;
    },
    getselectedDataset(state){  // 在组件中的调用方式:this_.$store.getters.getselectedDataset
      return state.egoOverview.selectedDataset;
    },
    getdatasetList(state){ // this.$store.getters.getdatasetList
      return state.selectDataset.datasetList;
    },
    gettimeStepList(state){ // this.$store.getters.gettimeStepList
      return state.timeLineSlice.timeStepList;
    },
    gettimeStepSlice(state){ // this.$store.getters.gettimeStepSlice
      return state.timeLineSlice.timeStepSlice;
    },
    getselectedEgoList(state){ // this_.$store.getters.getselectedEgoList
      return state.egoNetSequences.selectedEgoList;
    },
    getselectedDistance(state){ // this_.$store.getters.getselectedDistance
      return state.App.selectedDistance;
    },
    getselectedMethodRD(state){ // this_.$store.getters.getselectedMethodRD
      return state.App.selectedMethodRD;
    },
    getselectedMethodNorm(state){ // this_.$store.getters.getselectedMethodNorm
       return state.App.selectedMethodNorm;
    },    
    getfilterIterms(state){  // this_.$store.getters.getfilterIterms
      return state.App.filterIterms;
    },
    getgetCandidateAttrs(state){ // this_.$store.getters.getgetCandidateAttrs
      return state.App.getCandidateAttrs;
    },
    getfieldList(state){ // this_.$store.getters.getfieldList
      return state.searchBox.fieldList;
    },
    getcolorMap(state){ // this_.$store.getters.getcolorMap.egoColor
      return state.colorMap;
    },
    getegoPointPosition(state){ // this_.$store.getters.getegoPointPosition
      return state.searchBox.egoPointPosition;
    },
    getclickedEgoList(state){ // this_.$store.getters.getclickedEgoList
      return state.egoOverviewTimeStep.clickedEgoList;
    },
    getdateStringArray(state){ // this_.$store.getters.getdateStringArray
      return state.egoOverviewTimeStep.dateStringArray;
    },
    gettimeStepEgonetW(state){ // this_.$store.getters.gettimeStepEgonetW
      return state.egoOverviewTimeStep.timeStepEgonetW;
    },
    gettimeStepEgonetH(state){ // this_.$store.getters.gettimeStepEgonetH
      return state.egoOverviewTimeStep.timeStepEgonetH;
    },
    gettimeStepOverviewH(state){ // this_.$store.getters.gettimeStepOverviewH
      return state.egoOverviewTimeStep.timeStepOverviewH;
    },
    getcolorSchemeList(state){ // this_.$store.getters.getcolorSchemeList
      return state.timeCurveView.colorSchemeList;
    },
    getselectedEgoObj(state){ // this_.$store.getters.getselectedEgoObj
      return state.timeCurveView.selectedEgoObj;
    },
    getegoOverviewRt(state){ // this_.$store.getters.getegoOverviewRt
      return state.DOM.egoOverviewRt;
    },
    getegoOverviewTimeStepRt(state){ // this_.$store.getters.getegoOverviewTimeStepRt
      return state.DOM.egoOverviewTimeStepRt;
    },
    getegoNetSequenceRt(state){ // this_.$store.getters.getegoNetSequenceRt
      return state.DOM.egoNetSequenceRt;
    },
    getcolorSchemeObj(state){ // this_.$store.getters.getcolorSchemeObj
      return state.App.colorSchemeObj;
    },
    getcolorRadio(state){ // this_.$store.getters.getcolorRadio
      return state.App.colorRadio;
    },
    getattrRadio(state){ // this_.$store.getters.getattrRadio
      return state.App.attrRadio;
    },
    getfilterObj(state){ // this_.$store.getters.getfilterObj
      return state.App.filterObj;
    },
    getmarkRectTextList(state){ // this_.$store.getters.getmarkRectTextList
      return state.egoNetSequences.markRectTextList;
    }
  },
  mutations: {  // 对state中的状态进行修改.简化组件中对state的修改. 调用方式: this.$store.commit('changeSelection', mao); 
    changeselectedDataset(state, newState){ // this_.$store.commit('changeselectedDataset', mao);
      state.egoNetSequences.selectedEgoList.splice(0, state.egoNetSequences.selectedEgoList.length); // clear all elements
      state.egoOverview.selectedDataset = newState;
    },  
    changedatasetList(state, newdatasetList){ // newdatasetList=[x, x, ...]
      state.selectDataset.datasetList.splice(0, state.selectDataset.datasetList.length);
      for(let i=0; i < newdatasetList.length; i++){
         let item = newdatasetList[i];
         state.selectDataset.datasetList.push(item);
      }      
    },
    changetimeStepList(state, newdatasetList){ // this_.$store.commit('changetimeStepList', mao);      
      state.timeLineSlice.timeStepList.splice(0, state.timeLineSlice.timeStepList.length);
      for(let i=0; i < newdatasetList.length; i++){
         let item = newdatasetList[i];
         state.timeLineSlice.timeStepList.push(item);
      }
      state.timeLineSlice.timeStepSlice.splice(0, state.timeLineSlice.timeStepSlice.length); // clear all elements
      state.egoNetSequences.selectedEgoList.splice(0, state.egoNetSequences.selectedEgoList.length); // clear all elements
    },
    changetimeStepSlice(state, newdatasetList){ // this_.$store.commit("changetimeStepSlice", newdatasetList)
      state.timeLineSlice.timeStepSlice.splice(0, state.timeLineSlice.timeStepSlice.length); // 先清空之前的列表.
      for(let i=0; i < newdatasetList.length; i++){
         let item = newdatasetList[i];
         state.timeLineSlice.timeStepSlice.push(item);
      }      
    },
    clearselectedEgoList(state){
      state.egoNetSequences.selectedEgoList.splice(0, state.egoNetSequences.selectedEgoList.length); // clear all elements
    },
    removeOneselectedEgoList(state, index){ // this_.$store.commit("removeOneselectedEgoList", index)
      state.egoNetSequences.selectedEgoList.splice(index, 1); // 删除指定元素
    },
    changeselectedEgoList(state, newEgo){
      if (state.egoNetSequences.selectedEgoList.indexOf(newEgo) == -1){ // not in
         state.egoNetSequences.selectedEgoList.push(newEgo);
      }      
    },
    changeselectedDistance(state, newState){ // this_.$store.commit("changeselectedDistance", newState)
       state.App.selectedDistance = newState;
    },
    changeselectedMethodRD(state, newState){ // this_.$store.commit("changeselectedMethodRD", newState)
      state.App.selectedMethodRD = newState;
    },
    changeselectedMethodNorm(state, newState){ // this_.$store.commit("changeselectedMethodNorm", newState)
      // console.log("change selectedMethodNorm...");console.log(newState);
      state.App.selectedMethodNorm = newState;
    },    
    changefilterIterms(state, newState){ // this_.$store.commit("changefilterIterms", newState)
      state.App.filterIterms = newState;      
    },
    changefieldList(state, newState){ // this_.$store.commit("changefieldList", newState)
      state.searchBox.fieldList.splice(0, state.searchBox.fieldList.length);
      for(let i=0; i < newState.length; i++){
         let item = newState[i];
         state.searchBox.fieldList.push(item);
      }
    },
    changeegoPointPosition(state, newState){ // this_.$store.commit("changeegoPointPosition", newState)      
      state.searchBox.egoPointPosition = newState;
    },
    changeclickedEgoList(state, newEgo){ // this_.$store.commit("changeclickedEgoList", newEgo)
      if (state.egoOverviewTimeStep.clickedEgoList.indexOf(newEgo) == -1){ // not in
         state.egoOverviewTimeStep.clickedEgoList.push(newEgo);
      }
    },
    removeOneclickedEgoList(state, index){ // this_.$store.commit("removeOneclickedEgoList", index)
      state.egoOverviewTimeStep.clickedEgoList.splice(index, 1);
    },
    clearclickedEgoList(state){ // this_.$store.commit("clearclickedEgoList")
      state.egoOverviewTimeStep.clickedEgoList.splice(0, state.egoOverviewTimeStep.clickedEgoList.length); // clear all elements
    },
    changedateStringArray(state, newState){ // this_.$store.commit("changedateStringArray", newState)
      state.egoOverviewTimeStep.dateStringArray.splice(0, state.egoOverviewTimeStep.dateStringArray.length);
      for(let i=0; i < newState.length; i++){
         let item = newState[i];
         state.egoOverviewTimeStep.dateStringArray.push(item);
      }
    },
    addOneForselectedEgoObj(state, newState){ // this_.$store.commit("addOneForselectedEgoObj", newState);
      // newState = {key: val};
      let ego = Object.keys(newState)[0]; // ["key"]
      let egoName = newState[ego];
      state.timeCurveView.selectedEgoObj[ego] = egoName;
      // console.log("addForselectedEgoObj"); console.log(state.timeCurveView.selectedEgoObj);
    },
    removeOneselectedEgoObj(state, ego){ // 删除一个键值对. this_.$store.commit("removeOneselectedEgoObj", ego);
      // newState: ego
      delete state.timeCurveView.selectedEgoObj[ego];
      // console.log("removeOneselectedEgoObj"); console.log(state.timeCurveView.selectedEgoObj);
    },
    clearAllselectedEgoObj(state){ // this_.$store.commit("clearAllselectedEgoObj");
      for(let key in state.timeCurveView.selectedEgoObj){
        delete state.timeCurveView.selectedEgoObj[key];
      }
      // console.log("clearAllselectedEgoObj"); console.log(state.timeCurveView.selectedEgoObj);
    },    
    changeegoOverviewRt(state, newState){ // this_.$store.commit("changeegoOverviewRt", root);
      state.DOM.egoOverviewRt = newState;
    },    
    addOneegoOverviewTimeStepRt(state, newState){ // this_.$store.commit("addOneegoOverviewTimeStepRt", root);
      state.DOM.egoOverviewTimeStepRt.push(newState);
    },
    clearegoOverviewTimeStepRt(state){ // this_.$store.commit("clearegoOverviewTimeStepRt");
      state.DOM.egoOverviewTimeStepRt.splice(0, state.DOM.egoOverviewTimeStepRt.length); // 删除指定元素
    },
    addOneegoNetSequenceRt(state, newState){ // this_.$store.commit("addOneegoNetSequenceRt", [x, x, x, ...]);
      state.DOM.egoNetSequenceRt.push(newState);
    },
    removeOneegoNetSequenceRt(state, index){ // this_.$store.commit("removeOneegoNetSequenceRt", index);
      state.DOM.egoNetSequenceRt.splice(index, 1);
    },
    clearegoNetSequenceRt(state){ // this_.$store.commit("clearegoNetSequenceRt");
      state.DOM.egoNetSequenceRt.splice(0, state.DOM.egoNetSequenceRt.length); // 删除指定元素
    },
    changegetCandidateAttrs(state, newState){ // this_.$store.commit("changegetCandidateAttrs", newstate);
      state.App.getCandidateAttrs = newState;
    },
    changecolorRadio(state, newState){ // this_.$store.commit("changecolorRadio", newstate);
      state.App.colorRadio = newState;
    },
    changeattrRadio(state, newState){
      state.App.attrRadio = newState;
    },
    changefilterObj(state, newState){ // this_.$store.commit("changefilterObj", newstate);
      state.App.filterObj = newState;
    },
    changefeatureNameList(state, newState){ // this_.$store.commit("changefeatureNameList", newstate)
      state.stackedGraph.featureNameList = newState;
    },
    addOnemarkRectTextList(state, newState){ // this_.$store.commit("addOnemarkRectTextList", newstate)
      state.egoNetSequences.markRectTextList.push(newState);
    },
    removeOnemarkRectTextList(state, index){ // this_.$store.commit("removeOnemarkRectTextList", index)
      state.egoNetSequences.markRectTextList.splice(index, 1);
    },
    clearmarkRectTextList(state){ // // this_.$store.commit("clearmarkRectTextList")
      state.egoNetSequences.markRectTextList.splice(0, state.egoNetSequences.markRectTextList.length);
    }
  },
  actions: { // 对state进行异步修改,mutations的升级,用于异步,提高效率.
    asynchangedatasetList(context, newdatasetList){  // 调用方式:this.$store.dispatch('changeStateSelection', mao)
      context.commit("changedatasetList", newdatasetList);
    },
    asynchangetimeStepList(context, newdatasetList){
      context.commit("changetimeStepList", newdatasetList);
    }
  }
 
});

// 外部接口,外部使用时,格式如:import {xx, xx} from "xxx"
export {
    store // 在main.js中引用.
}